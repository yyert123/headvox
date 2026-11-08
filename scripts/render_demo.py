"""Render a karaoke-style preview GIF/MP4 frames from a HeadVox output folder.

Usage: python scripts/render_demo.py out/   (needs numpy + pillow; writes frames/*.png)
"""
import json, subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src=sys.argv[1]
d=json.load(open(f'{src}/voiceover.json'))
words=[w for s in d['segments'] for w in s['words']]
cues=d['cues']; dur=d['duration_ms']
pcm=subprocess.run(['ffmpeg','-v','error','-i',f'{src}/voiceover.mp3','-ac','1','-ar','8000','-f','s16le','-'],capture_output=True).stdout
a=np.frombuffer(pcm,dtype=np.int16).astype(np.float32)/32768
W,H=720,405; FPS=10; N=56
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; M="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
fC=ImageFont.truetype(B,26); fM=ImageFont.truetype(M,15); fS=ImageFont.truetype(R,13); fT=ImageFont.truetype(M,13)
bg=Image.new("RGB",(W,H),(11,12,16)); g=Image.new("RGB",(W,H),(0,0,0)); gd=ImageDraw.Draw(g)
gd.ellipse((-150,-250,500,200),fill=(50,35,120)); gd.ellipse((450,250,900,600),fill=(90,25,65))
bg=Image.blend(bg,g.filter(ImageFilter.GaussianBlur(110)),0.5)
def rms(t0,t1):
    s=a[max(0,int(t0*8)):max(0,int(t1*8))]; return float(np.sqrt((s**2).mean())) if len(s) else 0
peak=max(rms(i*50,i*50+50) for i in range(dur//50)) or 1
total=int(dur/1000*FPS)+6
for f in range(total):
    t=f*1000/FPS; im=bg.copy(); dr=ImageDraw.Draw(im)
    dr.text((28,24),"$ headvox demo-en.md -o out/ --voice en-US-AriaNeural",font=fM,fill=(255,140,180))
    bw=W/N
    for i in range(N):
        tt=t+(i-N//2)*80
        v=min(1,rms(tt,tt+80)/peak) if 0<=tt<dur else 0
        h=6+v*110; x=i*bw+3
        dr.rounded_rectangle((x,150-h/2,x+bw-6,150+h/2),3,fill=(155,130,255) if i<=N//2 else (70,74,96))
    cue=next((c for c in cues if c['start_ms']<=t<=c['end_ms']+150),None)
    if cue:
        cw=[w for w in words if cue['start_ms']-5<=w['start_ms']<=cue['end_ms']]
        toks=cue['text'].split(' ')
        widths=[dr.textlength(x+' ',font=fC) for x in toks]; tot=sum(widths)
        x=(W-tot)/2; y=262
        dr.rounded_rectangle((x-18,y-12,x+tot+8,y+44),12,fill=(0,0,0))
        for k,tok in enumerate(toks):
            active = k<len(cw) and cw[k]['start_ms']<=t
            dr.text((x,y),tok,font=fC,fill=(255,255,255) if active else (110,114,135))
            if k<len(cw) and cw[k]['start_ms']<=t<cw[k]['end_ms']:
                dr.rectangle((x,y+38,x+dr.textlength(tok,font=fC),y+41),fill=(255,140,180))
            x+=widths[k]
        dr.text((28,350),f"cue {cue['index']}  {cue['start_ms']/1000:06.3f} -> {cue['end_ms']/1000:06.3f}",font=fT,fill=(154,160,180))
    dr.text((28,372),"real, unedited output - word timings from voiceover.json",font=fS,fill=(120,126,146))
    dr.text((W-80,372),f"{t/1000:5.1f}s",font=fT,fill=(120,126,146))
    im.save(f"frames/{f:04d}.png")
print(total)
