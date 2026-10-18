import unittest,tempfile,struct,zlib,hashlib,json,base64,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
class PortableModTests(unittest.TestCase):
 def fixture(self,root):
  from mod import sha
  package=root/'package';package.mkdir();game=root/'game';game.mkdir();(game/'sce_sys').mkdir()
  keys=b'TITLE_ID\0APP_VER\0';values=b'CUSA03694\0' + b'01.11\0';ko=52;do=ko+len(keys)
  sfo=struct.pack('<5I',0x46535000,0x101,ko,do,2)+struct.pack('<HHIII',0,0x204,10,10,0)+struct.pack('<HHIII',9,0x204,6,6,10)+keys+values
  (game/'sce_sys/param.sfo').write_bytes(sfo);entries=[]
  for idx,aname in enumerate(['Gravite2_Chunk0.psarc','Gravite2_Patch_Chunk0.psarc']):
   name=f'gcd/test{idx}.bin';old=(f'original-{idx}'.encode())*8000;new=old[:10]+b'XBOX'+old[14:];contents=[(name+'\n').encode(),old];blocks=[];toc=32+60+6;off=toc;records=[]
   for j,data in enumerate(contents):
    chunks=[zlib.compress(data[k:k+65536]) for k in range(0,len(data),65536)]
    records.append(hashlib.md5((name if j else '').encode()).digest()+len(blocks).to_bytes(4,'big')+len(data).to_bytes(5,'big')+off.to_bytes(5,'big'));blocks+=chunks;off+=sum(map(len,chunks))
   raw=struct.pack('>4sI4s5I',b'PSAR',0x10004,b'zlib',toc,30,2,65536,0)+b''.join(records)+b''.join(len(x).to_bytes(2,'big') for x in blocks)+b''.join(blocks);(game/aname).write_bytes(raw)
   delta={'segments':[[10,14,base64.b64encode(b'XBOX').decode()]]};p=package/f'{idx}.json';p.write_text(json.dumps(delta));entries.append({'archive':aname,'name':name,'original_sha256':sha(old),'modified_sha256':sha(new),'modified_size':len(new),'delta':p.name,'delta_sha256':sha(p.read_bytes())})
  manifest={'title_id':'CUSA03694','app_ver':'01.11','files':entries};(package/'manifest.json').write_text(json.dumps(manifest));return package,game
 def test_install_check_idempotency_uninstall_exact(self):
  from mod import install,check,uninstall
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   package,game=self.fixture(Path(td));original={p.name:p.read_bytes() for p in game.glob('*.psarc')}
   self.assertEqual(check(game,package)['original'],2)
   backup=install(game,package,enforce_closed=False);self.assertIsNotNone(backup);self.assertEqual(check(game,package)['installed'],2)
   self.assertIsNone(install(game,package,enforce_closed=False))
   uninstall(game,backup,enforce_closed=False)
   for n,b in original.items():self.assertEqual((game/n).read_bytes(),b)
 def test_unknown_member_refused_before_any_write(self):
  from mod import install
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   package,game=self.fixture(Path(td));m=json.loads((package/'manifest.json').read_text());m['files'][1]['original_sha256']='0'*64;(package/'manifest.json').write_text(json.dumps(m));original={p.name:p.read_bytes() for p in game.glob('*.psarc')}
   with self.assertRaises(ValueError):install(game,package,enforce_closed=False)
   for n,b in original.items():self.assertEqual((game/n).read_bytes(),b)
 def test_second_archive_failure_rolls_back_first(self):
  import mod
  from unittest.mock import patch
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   package,game=self.fixture(Path(td));original={p.name:p.read_bytes() for p in game.glob('*.psarc')};real_apply=mod.apply;calls=[]
   def fail_second(path,plan,backup):
    calls.append(str(path))
    if len(calls)==2:raise OSError('simulated second archive write failure')
    return real_apply(path,plan,backup)
   with patch.object(mod,'apply',side_effect=fail_second):
    with self.assertRaises(OSError):mod.install(game,package,enforce_closed=False)
   for n,b in original.items():self.assertEqual((game/n).read_bytes(),b)
 def test_wrong_version_refused(self):
  from mod import check
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   package,game=self.fixture(Path(td));p=game/'sce_sys/param.sfo';p.write_bytes(p.read_bytes().replace(b'01.11',b'01.10'))
   with self.assertRaises(ValueError):check(game,package)
if __name__=='__main__':unittest.main()
