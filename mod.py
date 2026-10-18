"""Gravity Rush 2 Xbox button patches. Python 3.10+, standard library only."""
import argparse,base64,csv,datetime,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
from psarc import Archive,prepare,apply,restore,digest
PACKAGE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def closed():
 names=[]
 if os.name=='nt':
  out=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace');names=[r[0].lower() for r in csv.reader(out.splitlines()) if r]
 elif Path('/proc').is_dir():
  for p in Path('/proc').iterdir():
   if p.name.isdigit():
    try:names.append((p/'comm').read_text().strip().lower())
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 if any('shad' in n or 'gr2fork' in n or n.startswith('eboot') for n in names):raise ValueError('Close the game and emulator before installing or uninstalling.')

def version(game):
 b=(game/'sce_sys/param.sfo').read_bytes();magic,_,ks,ds,n=struct.unpack_from('<5I',b)
 if magic!=0x46535000:raise ValueError('Invalid param.sfo')
 fields={}
 for i in range(n):
  ko,fmt,ln,mx,do=struct.unpack_from('<HHIII',b,20+i*16);key=b[ks+ko:].split(b'\0')[0].decode();fields[key]=b[ds+do:ds+do+ln].rstrip(b'\0').decode(errors='replace')
 return fields.get('TITLE_ID'),fields.get('APP_VER')

def inspect(game,package):
 game=Path(game).resolve();package=Path(package).resolve();manifest=json.loads((package/'manifest.json').read_text())
 if version(game)!=(manifest['title_id'],manifest['app_ver']):raise ValueError('This mod requires CUSA03694 version 01.11. Other versions will not be modified.')
 archives={};rows=[]
 for item in manifest['files']:
  aname=item['archive'];name=item['name']
  if Path(aname).name!=aname:raise ValueError('Invalid archive filename')
  if aname not in archives:archives[aname]=Archive(game/aname)
  data=archives[aname].extract(name);current=sha(data)
  if current==item['modified_sha256']:state='installed'
  elif current==item['original_sha256']:state='original'
  else:raise ValueError('Incompatible resource or resource changed by another mod: '+aname+' / '+name)
  rows.append((item,data,state))
 return game,package,rows

def check(game,package=PACKAGE):
 _,_,rows=inspect(game,package)
 return {state:sum(row[2]==state for row in rows) for state in ['original','installed']}

def install(game,package=PACKAGE,enforce_closed=True):
 if enforce_closed:closed()
 game,package,rows=inspect(game,package);groups={}
 for item,data,state in rows:
  if state=='installed':continue
  delta_path=(package/item['delta']).resolve()
  if not delta_path.is_relative_to(package):raise ValueError('Invalid patch path')
  delta_bytes=delta_path.read_bytes()
  if sha(delta_bytes)!=item['delta_sha256']:raise ValueError('Damaged patch: '+item['delta'])
  delta=json.loads(delta_bytes);out=bytearray();cursor=0
  for start,end,encoded in delta['segments']:
   if not cursor<=start<=end<=len(data):raise ValueError('Invalid delta')
   out.extend(data[cursor:start]);out.extend(base64.b64decode(encoded,validate=True));cursor=end
  out.extend(data[cursor:]);out=bytes(out)
  if len(out)!=item['modified_size'] or sha(out)!=item['modified_sha256']:raise ValueError('Reconstructed resource does not match: '+item['name'])
  groups.setdefault(item['archive'],{})[item['name']]=out
 if not groups:print('The changes are already installed; no patches were reapplied.');return None
 # Preflight ALL archives before any write. The existing block table is never resized.
 plans={name:prepare(game/name,files) for name,files in groups.items()}
 backup=game/'.gr2-xbox-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup.mkdir(parents=True)
 transaction={'game':str(game),'archives':[],'state':'installing'};(backup/'transaction.json').write_text(json.dumps(transaction,indent=2),encoding='utf-8')
 applied=[]
 try:
  for name,plan in plans.items():
   if enforce_closed:closed()
   folder=backup/name;apply(game/name,plan,folder);applied.append(name);transaction['archives'].append(name)
   (backup/'transaction.json').write_text(json.dumps(transaction,indent=2),encoding='utf-8')
  state=check(game,package)
  if state['original']:raise ValueError('Final verification incomplete')
  transaction['state']='installed';(backup/'transaction.json').write_text(json.dumps(transaction,indent=2),encoding='utf-8')
 except BaseException:
  for name in reversed(applied):restore(game/name,backup/name)
  transaction['state']='rolled_back';(backup/'transaction.json').write_text(json.dumps(transaction,indent=2),encoding='utf-8');raise
 print('Installation verified. Reversible backup: '+str(backup));return backup

def uninstall(game,backup,enforce_closed=True):
 if enforce_closed:closed()
 game=Path(game).resolve();backup=Path(backup).resolve();tx=json.loads((backup/'transaction.json').read_text(encoding='utf-8'))
 if tx['game']!=str(game) or tx['state']!='installed':raise ValueError('Invalid backup for this installation')
 for name in tx['archives']:
  r=json.loads((backup/name/'receipt.json').read_text())
  if digest(game/name)!=r['installed_sha256']:raise ValueError('The archive changed after mod installation. Refusing to restore to avoid losing other changes: '+name)
  if sha((backup/name/'original-toc.bin').read_bytes())!=r['toc_sha256']:raise ValueError('Damaged backup')
 for name in reversed(tx['archives']):
  if enforce_closed:closed()
  restore(game/name,backup/name)
 tx['state']='uninstalled';(backup/'transaction.json').write_text(json.dumps(tx,indent=2),encoding='utf-8');print('Mod uninstalled; original archive hashes restored.')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',nargs='?',default='install',choices=['install','check','uninstall']);p.add_argument('game',nargs='?',type=Path);p.add_argument('--backup',type=Path);a=p.parse_args()
 game=a.game or Path(input('Game folder (containing eboot.bin and sce_sys): ').strip().strip('"'))
 if a.action=='check':print(json.dumps(check(game),indent=2))
 elif a.action=='install':install(game)
 else:
  backup=a.backup
  if backup is None:
   candidates=[]
   for q in (game/'.gr2-xbox-backups').glob('*/transaction.json'):
    if json.loads(q.read_text(encoding='utf-8')).get('state')=='installed':candidates.append(q.parent)
   if not candidates:raise ValueError('No active backup found; use --backup PATH')
   backup=max(candidates,key=lambda q:q.name)
  uninstall(game,backup)
if __name__=='__main__':
 try:main()
 except (Exception,KeyboardInterrupt) as e:print('ERROR: '+str(e),file=sys.stderr);sys.exit(1)
