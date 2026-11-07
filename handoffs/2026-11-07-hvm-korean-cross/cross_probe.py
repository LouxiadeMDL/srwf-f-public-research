"""Read-only cross-source probes: original F functions, synthetic RAM.
No ROM patches, saves or emulator gameplay. Original inputs remain unchanged.
"""
from pathlib import Path
import sys,json,hashlib,argparse
W=Path(__file__).resolve().parent
CPU_SHA='588686ebb6a16c7a9f5bc2d0b893d492c79ea3334c02e5a001a7921add3edf30'
CPU_PATH=W/'.local_inputs/vendor/sh2_subset.py'
if not CPU_PATH.is_file() or hashlib.sha256(CPU_PATH.read_bytes()).hexdigest()!=CPU_SHA:
 raise SystemExit('Run prepare_input.py with the documented local archive first')
sys.path.insert(0,str(CPU_PATH.parent))
from sh2_subset import Memory,CPU,MASK,s32
class AlignmentError(ValueError): pass
class StrictMemory(Memory):
 def read(self,a,n):
  if n in (2,4) and a%n:raise AlignmentError(f'unaligned read {a:08X}/{n}')
  return super().read(a,n)
 def write(self,a,n,v):
  if n in (2,4) and a%n:raise AlignmentError(f'unaligned write {a:08X}/{n}')
  return super().write(a,n,v)
class CrossCPU(CPU):
 def step(self,delay=False):
  pc=self.pc;op=self.m.read(pc,2);n=(op>>8)&15;m=(op>>4)&15
  # Narrow missing CPU operations, never game-function callee hooks.
  if op&0xf00f==0x0007:
   self.m.pc=pc;self.steps+=1;self.trace.append((pc,op));self.pc=pc+2
   self.macl=(self.r[n]*self.r[m])&MASK;return
  if op&0xf0ff in (0x4015,0x4011):
   self.m.pc=pc;self.steps+=1;self.trace.append((pc,op));self.pc=pc+2
   self.t=int(s32(self.r[n])>0 if op&255==0x15 else s32(self.r[n])>=0);return
  return super().step(delay)
def mem():
 code=(W/'.local_inputs/EXEC0.bin').read_bytes()
 if hashlib.sha256(code).hexdigest()!='a7e9a648641d728dcf6f60a778d6a1e5ccfebc77c92a0d3fd64cbcd5f19db409':raise ValueError('EXEC identity mismatch')
 m=StrictMemory(b'');m.regions=[];hi=bytearray(0x100000);hi[0x4000:0x4000+len(code)]=code
 m.map(0x06000000,len(hi),'high',hi);m.map(0x20200000,0x100000,'low');m.map(0x10000000,0x1000,'args')
 for a,v in [(0x060B2090,0x20200000),(0x060B2088,0x202005A0),(0x060B208C,0x202014A0),(0x060B207C,0x20201AA0),(0x060C0900,0x10000000)]:m.write(a,4,v)
 for i in range(74):m.write(0x20201aa0+i*16,1,255)
 for j,pid,actor,faction in [(0,0x7e,3,0),(1,0x84,5,1)]:
  p=0x202014a0+j*12;u=0x202005a0+j*30;a=0x20201aa0+actor*16
  m.write(p,2,pid);m.write(p+3,1,0);m.write(p+8,1,255);m.write(p+9,1,100)
  m.write(u,2,0x100+j);m.write(u+15,1,j);m.write(u+16,1,255)
  m.write(a,1,10+j);m.write(a+1,1,20);m.write(a+2,1,j);m.write(a+3,1,faction<<1)
 m.write(0x060C0715,1,0x35);m.write(0x060C0704,4,0x77777777);m.writes=[]
 return m
def call(m,args,entry):
 for i,x in enumerate(args):m.write(0x10000000+i,1,x)
 m.writes=[];c=CrossCPU(m);r=c.run(entry,100000);return {'instructions':r['steps'],'R0':hex(r['r0']),'predicate_bit7':bool(m.read(0x060C0715,1)&128),'numeric':m.read(0x060C0704,4),'hooks':r['hooks'],'trace_sha256':r['trace_sha256'],'store_count':len(r['writes']),'low_stores':[w for w in r['writes'] if w['region']=='low']}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path);dest=parser.parse_args().out
 if dest.exists():raise SystemExit('Refusing to overwrite an existing output')
 if not dest.resolve().is_relative_to((W/'.local_results').resolve()):raise SystemExit('Output must be under this handoff .local_results directory')
 out={'scope':'original F native functions on synthetic RAM only','cases':[],'alignment':[]}
 for pair,operands in [((3,5),(0x7e,0x84)),((5,3),(0x7e,0x84)),((3,5),(0x84,0x7e)),((5,3),(0x84,0x7e)),((3,3),(0x7e,0x84)),((3,3),(0x7e,0x7e))]:
  m=mem();m.write(0x060c0694,1,pair[0]);m.write(0x060c0695,1,pair[1]);a=b'\x01'+b''.join(x.to_bytes(2,'big')for x in operands)
  try:r=call(m,a,0x0601e3c4);out['cases'].append({'type':'EB.01','pair':pair,'selectors':[hex(x)for x in operands],**r});print('EB',pair,operands,r['predicate_bit7'],r['instructions'])
  except Exception as e:print('EB failure',type(e).__name__,e);raise
 for item,initial in [(10,0),(10,8),(10,9),(10,255),(29,0),(30,0)]:
  m=mem();m.write(0x20200574+item,1,initial);r=call(m,bytes([0x0e,item]),0x0602bb80)
  out['cases'].append({'type':'C2.0E','item':item,'initial':initial,'after':m.read(0x20200574+item,1),**r});print('ITEM',item,initial,out['cases'][-1]['after'])
 for selector in [0x7e,0x84,0x1ee]:
  m=mem();r=call(m,b'\x0a'+selector.to_bytes(2,'big'),0x06028894);out['cases'].append({'type':'C1.0A','selector':hex(selector),**r});print('C10A',hex(selector),r['predicate_bit7'],r['numeric'])
 for cls in [Memory,StrictMemory]:
  for addr in [0x20000000,0x20000002]:
   m=cls(bytes.fromhex('6012000b0009'));m.map(0x20000000,16,'data',bytes(range(16)));c=CPU(m);c.r[1]=addr
   try:r=c.run(0x06004000);out['alignment'].append({'memory':cls.__name__,'address':hex(addr),'outcome':'RETURNED','value':hex(r['r0'])})
   except AlignmentError as e:out['alignment'].append({'memory':cls.__name__,'address':hex(addr),'outcome':'REJECTED','message':str(e)})
 dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('Wrote',len(out['cases']),'native cases;',len(out['alignment']),'alignment cases')
if __name__=='__main__':main()
