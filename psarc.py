from pathlib import Path
import struct,zlib
class Archive:
 def __init__(self,path):
  self.path=path
  with path.open('rb') as f:
   self.header=f.read(32)
   magic,ver,comp,self.toc,self.es,self.n,self.bs,flags=struct.unpack('>4sI4s5I',self.header)
   assert magic==b'PSAR' and comp==b'zlib' and self.es==30
   self.table=f.read(self.toc-32)
  self.sizes=self.table[self.n*self.es:];self.nb=(self.bs.bit_length()-1+7)//8
  self.names=self.extract_index(0).decode().splitlines();assert len(self.names)==self.n-1
 def extract_index(self,i):
  e=self.table[i*self.es:(i+1)*self.es];idx=int.from_bytes(e[16:20],'big');ln=int.from_bytes(e[20:25],'big');off=int.from_bytes(e[25:30],'big');out=bytearray()
  with self.path.open('rb') as f:
   while len(out)<ln:
    sz=int.from_bytes(self.sizes[idx*self.nb:(idx+1)*self.nb],'big') or self.bs;f.seek(off);d=f.read(sz)
    if sz!=self.bs:
     try:d=zlib.decompress(d)
     except zlib.error:pass
    out.extend(d);off+=sz;idx+=1
  assert len(out)>=ln
  return bytes(out[:ln])
 def extract(self,name):return self.extract_index(self.names.index(name)+1)

"""Reversible PSARC entry replacement, preserving all existing payload bytes."""
import hashlib,json,os,zlib
from pathlib import Path

def digest(path,start=0,end=None):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  f.seek(start)
  while end is None or f.tell()<end:
   b=f.read(8*1024*1024 if end is None else min(8*1024*1024,end-f.tell()))
   if not b:break
   h.update(b)
 return h.hexdigest()

def prepare(path,replacements):
 path=Path(path);a=Archive(path);size=path.stat().st_size;toc=bytearray(a.table);payload=bytearray();info=[]
 for name,data in sorted(replacements.items()):
  i=a.names.index(name)+1;e=bytearray(toc[i*a.es:(i+1)*a.es]);idx=int.from_bytes(e[16:20],'big');oldlen=int.from_bytes(e[20:25],'big')
  assert (oldlen+a.bs-1)//a.bs==(len(data)+a.bs-1)//a.bs,'Block counts must match; no global table relocation allowed'
  padding=(-(size+len(payload)))%2048;payload.extend(bytes(padding));offset=size+len(payload)
  for j,at in enumerate(range(0,len(data),a.bs)):
   raw=data[at:at+a.bs];compressed=zlib.compress(raw,9)
   if len(compressed)>=a.bs:
    assert len(raw)==a.bs
    block=raw;length=0
   else:block=compressed;length=len(block)
   p=a.n*a.es+(idx+j)*a.nb;toc[p:p+a.nb]=length.to_bytes(a.nb,'big');payload.extend(block)
  e[20:25]=len(data).to_bytes(5,'big');e[25:30]=offset.to_bytes(5,'big');toc[i*a.es:(i+1)*a.es]=e
  info.append({'name':name,'old_length':oldlen,'new_length':len(data),'sha256':hashlib.sha256(data).hexdigest(),'offset':offset})
 return {'original_size':size,'original_toc':a.header+a.table,'new_toc':a.header+toc,'payload':bytes(payload),'files':info,'original_sha256':digest(path),'original_body_sha256':digest(path,a.toc,size)}

def apply(path,plan,backup):
 path=Path(path);backup=Path(backup)
 assert path.stat().st_size==plan['original_size'] and digest(path)==plan['original_sha256'],'Archive changed since preparation'
 backup.mkdir(parents=True,exist_ok=False)
 (backup/'original-toc.bin').write_bytes(plan['original_toc'])
 receipt={k:plan[k] for k in ['original_size','original_sha256','original_body_sha256','files']};receipt['archive']=str(path.resolve());receipt['toc_sha256']=hashlib.sha256(plan['original_toc']).hexdigest()
 (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert (backup/'original-toc.bin').read_bytes()==plan['original_toc']
 try:
  with path.open('r+b') as f:
   f.seek(plan['original_size']);f.write(plan['payload']);f.flush();os.fsync(f.fileno())
   f.seek(0);f.write(plan['new_toc']);f.flush();os.fsync(f.fileno())
  a=Archive(path)
  assert digest(path,a.toc,plan['original_size'])==plan['original_body_sha256']
  for info in plan['files']:assert hashlib.sha256(a.extract(info['name'])).hexdigest()==info['sha256']
  receipt['installed_size']=path.stat().st_size;receipt['installed_sha256']=digest(path)
  (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 except BaseException:
  restore(path,backup,allow_incomplete=True)
  raise
 return receipt

def restore(path,backup,allow_incomplete=False):
 path=Path(path);backup=Path(backup);r=json.loads((backup/'receipt.json').read_text());toc=(backup/'original-toc.bin').read_bytes()
 assert str(path.resolve())==r['archive'];assert hashlib.sha256(toc).hexdigest()==r['toc_sha256']
 if not allow_incomplete:assert digest(path)==r['installed_sha256'],'Archive changed since mod installation; refuse unsafe rollback'
 with path.open('r+b') as f:
  f.seek(0);f.write(toc);f.truncate(r['original_size']);f.flush();os.fsync(f.fileno())
 assert digest(path)==r['original_sha256']

