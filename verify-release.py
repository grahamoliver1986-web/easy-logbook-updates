import os,re,hashlib,urllib.request,urllib.parse,zipfile,io,pathlib,subprocess,json
url=os.environ['ARCHIVE_URL'];host=urllib.parse.urlparse(url)
assert host.scheme=='https' and host.username is None
assert host.hostname.endswith(('.oaiusercontent.com','.blob.core.windows.net','.actions.githubusercontent.com'))
sha=os.environ['ARCHIVE_SHA256'];assert re.fullmatch('[a-f0-9]{64}',sha)
version=os.environ['VERSION_NAME'];assert re.fullmatch(r'\d+(\.\d+){1,2}',version)
code=int(os.environ['VERSION_CODE']);assert code>0
with urllib.request.urlopen(url,timeout=45) as r:
 data=r.read(40000001)
assert len(data)<=40000000 and hashlib.sha256(data).hexdigest()==sha
z=zipfile.ZipFile(io.BytesIO(data));out=pathlib.Path('release');out.mkdir()
entries={pathlib.PurePosixPath(n).name:n for n in z.namelist() if n.endswith('.apk')}
assert set(entries)=={f'Easy-Logbook-{version}-Phone.apk',f'Easy-Logbook-{version}-Car.apk'}
android=pathlib.Path(os.environ['ANDROID_HOME'])/'build-tools'
tools=sorted(android.iterdir(),key=lambda p:[int(x) if x.isdigit() else 0 for x in re.split('[.-]',p.name)])[-1]
variants={}
expected='9fd0e03735453b9a7e0bf7675b811d69b319c8ea3d2a128e39c86b6cda60f166'
for role in ['car','phone']:
 name=f'Easy-Logbook-{version}-{role.title()}.apk';entry=z.getinfo(entries[name]);assert 0<entry.file_size<=30000000
 p=out/name;p.write_bytes(z.read(entry))
 cert=subprocess.check_output([str(tools/'apksigner'),'verify','--verbose','--print-certs',str(p)],text=True)
 assert f'Signer #1 certificate SHA-256 digest: {expected}' in cert
 badge=subprocess.check_output([str(tools/'aapt'),'dump','badging',str(p)],text=True)
 assert f"name='appinventor.ai_grahamoliver1986.EasyLogbook05' versionCode='{code}' versionName='{version}'" in badge.splitlines()[0]
 with zipfile.ZipFile(p) as apk:
  assert apk.read('assets/device-role.txt').decode().strip()==role
  assert not any(n.lower().endswith(('.jks','.keystore')) for n in apk.namelist())
  if role=='phone':assert apk.read('assets/car-installer.apk')==(out/f'Easy-Logbook-{version}-Car.apk').read_bytes()
 variants[role]={'version':code,'name':version,'flavor':role,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'url':f'https://github.com/grahamoliver1986-web/easy-logbook-updates/releases/download/v{version}/{name}'}
(out/'latest.json').write_text(json.dumps({'schema':1,'package':'appinventor.ai_grahamoliver1986.EasyLogbook05','variants':variants},indent=2)+'\n')
print('PASS: original signer, package, versions, roles, embedded car installer and artifact checksum. Ready to publish.')
