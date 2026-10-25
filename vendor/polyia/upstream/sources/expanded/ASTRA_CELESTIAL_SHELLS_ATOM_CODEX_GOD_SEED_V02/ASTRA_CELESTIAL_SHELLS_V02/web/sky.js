/* ASTRA Celestial Shells / software geometric fabric. No external sky textures.
   Physical star directions: ICRS (RA, Dec), J2000 samples. All shell radii and
   nonstellar destinations are explicitly schematic. Every glyph is selectable.
*/
(function(global){
'use strict';
const TAU=Math.PI*2, DEG=Math.PI/180;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function vec(ra,dec,r=1){let a=ra*DEG,d=dec*DEG;return [Math.cos(d)*Math.sin(a)*r,Math.sin(d)*r,Math.cos(d)*Math.cos(a)*r]}
function rotate(v,yaw,pitch){let [x,y,z]=v,cs=Math.cos(yaw),sn=Math.sin(yaw);let a=x*cs-z*sn,b=x*sn+z*cs;let cp=Math.cos(pitch),sp=Math.sin(pitch);return [a,y*cp-b*sp,y*sp+b*cp]}
function project(v,w,h,d=3.9){let z=d-v[2];if(z<.4)return null;let f=Math.min(w,h)*1.43;return {x:w*.5+v[0]*f/z,y:h*.51-v[1]*f/z,depth:v[2],scale:f/z}}
function hashnoise(i){let t=Math.sin(i*127.1+43.7)*43758.5453;return t-Math.floor(t)}
const DEST={Earth:{ra:0,dec:0,description:'Reference observation position · Earth centered. No live atmosphere or ephemerides.'},Moon:{ra:119,dec:18,description:'Modeled destination · lunar physical position not yet from Horizons.'},Mars:{ra:79,dec:14,description:'Modeled planet waypoint · this is not current Mars ephemeris.'},Jupiter:{ra:219,dec:-17,description:'Modeled planet waypoint · not a measured current sky position.'},Saturn:{ra:295,dec:12,description:'Modeled planet waypoint · not current JPL position.'},Neptune:{ra:343,dec:-9,description:'Modeled planet waypoint · no measured ephemeris loaded.'},ISS:{ra:169,dec:41,description:'Illustrative space station marker. Not a TLE prediction or real pass.'},'Milky Way':{ra:265,dec:-29,description:'Milky Way direction toward Galactic Center. Navigational sample; no physical travel simulation.'}};
class SkyEngine {
 constructor(rows){this.stars=(rows||[]).map((a,i)=>({id:'HIP '+a[0],name:'HIP '+a[0],ra:a[1],dec:a[2],mag:a[3],bv:a[4],type:'catalog',description:'Hipparcos apparent direction (ICRS/J2000); magnitude '+a[3]+'. Distance has not been inferred.',v:vec(a[1],a[2],1.65)}));
 this.planets=Object.entries(DEST).filter(([k])=>k!=='Earth').map(([name,x])=>({name,...x,type:'schematic',v:vec(x.ra,x.dec,1.90)}));
 this.level=0;this.grid=true;this.yaw=0.15;this.pitch=0.11;this.desiredYaw=.15;this.desiredPitch=.11;this.cameraDistance=4.25;this.targetDistance=4.25;this.autorotate=true;this.selectHandler=()=>{};this.stateHandler=()=>{};this.hit=[];this.drag=null;this.last={w:0,h:0};this.neighborhood='INNER OBSERVATORY';this.distanceMode='MODELED RADII';this.selected='Earth';this.frameSamples=[];this.sourceKind='bright-star ICRS';this.shellNames=['INNER OBSERVATORY','LOCAL CONSTELLATION','SOLAR NEIGHBORHOOD','GALACTIC STRUCTURE'];this.stars.sort((a,b)=>a.mag-b.mag);
 this.lines=[]; // derived nearest-neighbor visual connections; NOT IAU constellation lines
 for(let i=0;i<this.stars.length;i++){let a=this.stars[i],near=[];for(let j=0;j<this.stars.length;j++)if(i!==j){let b=this.stars[j],c=a.v[0]*b.v[0]+a.v[1]*b.v[1]+a.v[2]*b.v[2];near.push([c,j])}near.sort((a,b)=>b[0]-a[0]);for(let k=0;k<Math.min(2,near.length);k++)if(near[k][0]>1.65*1.65*.972&&near[k][1]>i)this.lines.push([i,near[k][1]]);}
 }
 setSelectHandler(fn){this.selectHandler=fn}
 setStateHandler(fn){this.stateHandler=fn;this.emit()}
 emit(){this.neighborhood=this.shellNames[this.level];this.stateHandler(this.diagnostic())}
 diagnostic(){return {level:this.level,neighborhood:this.neighborhood,distanceMode:this.distanceMode,starCount:this.stars.length,rendering:'CPU spherical geometry + optional WebGL2 stellar points',catalog:'Hipparcos ICRS directions, bright sample',ephemerides:'NOT_CONNECTED',selected:this.selected,grid:this.grid,yaw:this.yaw,pitch:this.pitch,auto:this.autorotate}}
 expand(){this.level=clamp(this.level+1,0,3);this.targetDistance=[4.25,3.60,3.15,2.80][this.level];this.emit()}
 contract(){this.level=clamp(this.level-1,0,3);this.targetDistance=[4.25,3.60,3.15,2.80][this.level];this.emit()}
 travel(dest){const v=DEST[dest];if(!v)return false;this.selected=dest;this.level=dest==='Milky Way'?3:dest==='Earth'?0:2;this.targetDistance=[4.25,3.60,3.15,2.8][this.level];this.desiredYaw= v.ra*DEG*.22;this.desiredPitch=v.dec*DEG*.5;this.emit();this.selectHandler({name:dest,type:'schematic',description:v.description});return true}
 attach(el){this.element=el;el.style.touchAction='pan-y';el.addEventListener('pointerdown',e=>{if(e.target.closest?.('button, input, select'))return;this.drag={x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,moved:0};el.setPointerCapture?.(e.pointerId)});el.addEventListener('pointermove',e=>{if(!this.drag)return;let dx=e.clientX-this.drag.lastX,dy=e.clientY-this.drag.lastY;this.desiredYaw+=dx*.007;this.desiredPitch=clamp(this.desiredPitch+dy*.005,-1.25,1.25);this.drag.lastX=e.clientX;this.drag.lastY=e.clientY;this.drag.moved+=Math.abs(dx)+Math.abs(dy);this.autorotate=false});el.addEventListener('pointerup',e=>{if(!this.drag)return;let r=el.getBoundingClientRect();if(this.drag.moved<12)this.pick(e.clientX-r.left,e.clientY-r.top);this.drag=null});el.addEventListener('wheel',e=>{e.preventDefault();if(e.deltaY<0)this.expand();else this.contract()},{passive:false});}
 pick(x,y){let best=null,dist=Infinity;for(const a of this.hit){const d=Math.hypot(a.x-x,a.y-y);if(d<dist){dist=d;best=a}}if(best&&dist<24){this.selected=best.node.name;this.selectHandler(best.node);return best.node}return null}
 transform(v){return rotate(v,this.yaw,this.pitch)}
 screen(v,w,h){return project(this.transform(v),w,h,this.cameraDistance)}
 draw(ctx,w,h,t){if(!ctx)return;this.last={w,h};ctx.clearRect(0,0,w,h);ctx.save();ctx.fillStyle='rgba(2,8,23,.88)';ctx.fillRect(0,0,w,h);
  const a=1-Math.exp(-Math.max(.001,1/60)*5);this.yaw+=(this.desiredYaw-this.yaw)*a;this.pitch+=(this.desiredPitch-this.pitch)*a;this.cameraDistance+=(this.targetDistance-this.cameraDistance)*a;if(this.autorotate){this.desiredYaw+=.0008;this.desiredPitch=Math.sin(t*.09)*.065}
  // Dim volumetric field: a visual function, not measured Milky Way matter.
  let g=ctx.createRadialGradient(w*.49,h*.54,5,w*.49,h*.54,Math.max(w,h)*.55);g.addColorStop(0,'rgba(22,84,110,.16)');g.addColorStop(.32,'rgba(14,63,92,.12)');g.addColorStop(.7,'rgba(34,24,86,.10)');g.addColorStop(1,'rgba(0,6,18,0)');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  this.renderGraticule(ctx,w,h,t);this.renderThreads(ctx,w,h,t);this.renderNebula(ctx,w,h,t);this.renderDust(ctx,w,h,t);this.renderObjects(ctx,w,h,t);ctx.restore();}
 renderGraticule(ctx,w,h,t){if(!this.grid)return;for(let layer=0;layer<=this.level+1;layer++){let radius=1.1+layer*.29;let alpha=.09+layer*.006;ctx.strokeStyle=`rgba(${layer%2?'108,162,198':'92,210,196'},${alpha})`;ctx.lineWidth=.6;for(let latitude=-60;latitude<=60;latitude+=30){ctx.beginPath();let opened=false;for(let i=0;i<=150;i++){let lon=i/150*360,p=this.screen(vec(lon,latitude,radius),w,h);if(!p)continue;if(!opened){ctx.moveTo(p.x,p.y);opened=true}else ctx.lineTo(p.x,p.y)}ctx.stroke()}
   for(let longitude=0;longitude<360;longitude+=30){ctx.beginPath();let started=false;for(let i=-90;i<=90;i+=3){let p=this.screen(vec(longitude,i,radius),w,h);if(!p)continue;if(!started){ctx.moveTo(p.x,p.y);started=true}else ctx.lineTo(p.x,p.y)}ctx.stroke()}
  }}
 renderThreads(ctx,w,h,t){ctx.lineWidth=.72;for(let [i,j] of this.lines){let a=this.screen(this.stars[i].v,w,h),b=this.screen(this.stars[j].v,w,h);if(!a||!b)continue;ctx.strokeStyle='rgba(220,179,105,.25)';ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
  // Generative filaments around a hierarchy of 3D angular anchors.
  const count=20+this.level*20;for(let k=0;k<count;k++){let lat=-53+hashnoise(k+40)*105,lon=hashnoise(k+15)*360,p1=this.screen(vec(lon,lat,1.24+this.level*.22),w,h),p2=this.screen(vec(lon+7+Math.sin(t*.3+k)*2,lat+4,1.24+this.level*.22),w,h);if(!p1||!p2)continue;ctx.strokeStyle=`rgba(87,199,185,${.018+.026*Math.sin(t*.34+k)**2})`;ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.quadraticCurveTo((p1.x+p2.x)*.5+9,(p1.y+p2.y)*.5,p2.x,p2.y);ctx.stroke()}}
 renderNebula(ctx,w,h,t){ctx.globalCompositeOperation='screen';for(let k=0;k<8+this.level*3;k++){let pos=this.screen(vec((k*37.41+60+t*.1)%360,Math.sin(k*2.4)*42,1.15+this.level*.16),w,h);if(!pos)continue;let r=Math.max(20,35+this.level*17)*pos.scale*.5;let g=ctx.createRadialGradient(pos.x,pos.y,0,pos.x,pos.y,r);let hue=k%2===0?'109,211,196':'93,105,187';g.addColorStop(0,`rgba(${hue},.035)`);g.addColorStop(1,`rgba(${hue},0)`);ctx.fillStyle=g;ctx.fillRect(pos.x-r,pos.y-r,r*2,r*2)}ctx.globalCompositeOperation='source-over'}
 renderDust(ctx,w,h,t){ // aesthetic star dust; not catalog stars
   for(let k=0;k<320+this.level*90;k++){
     let longitude=hashnoise(k*3+3)*360,latitude=(hashnoise(k*5+6)-.5)*154,
       r=1.5+.55*hashnoise(k*13+9),p=this.screen(vec(longitude,latitude,r),w,h);
     if(!p||p.x<0||p.x>w||p.y<0||p.y>h)continue;
     const alpha=(.10+hashnoise(k*11+1)*.35)*(Math.sin(t*.23+k*.7)*.13+.87);
     ctx.fillStyle=`rgba(${k%7===0?'255,209,127':'133,185,215'},${alpha})`;
     let rad=k%19===0?1.5:k%5===0?.85:.46;
     ctx.beginPath();ctx.arc(p.x,p.y,rad,0,TAU);ctx.fill();
   }
 }
 renderObjects(ctx,w,h,t){this.hit=[];
 // Real ICRS bright-star positions. GPU path owns point brightness; Canvas fallback still draws.
 for(let i=0;i<this.stars.length;i++){const n=this.stars[i],p=this.screen(n.v,w,h);if(!p||p.x<-20||p.x>w+20||p.y<-20||p.y>h+20)continue;let r=clamp((3.4-n.mag*.29)*p.scale, .45,2.4);ctx.fillStyle='rgba(204,239,252,.66)';ctx.shadowBlur=i<12?8:0;ctx.shadowColor='#9ceded';ctx.beginPath();ctx.arc(p.x,p.y,r,0,TAU);ctx.fill();this.hit.push({node:n,...p})}
 ctx.shadowBlur=0;
 for(let i=0;i<this.planets.length;i++){let n=this.planets[i],v=n.v,p=this.screen(v,w,h);if(!p||p.x<-40||p.x>w+40||p.y<-40||p.y>h+40)continue;let chosen=this.selected===n.name,r=clamp(5.5*p.scale,2.5,6.5);const color=(n.name==='ISS'?'#d1efec':i%2?'#76d9d0':'#ecbf7c');ctx.strokeStyle=chosen?'rgba(127,249,220,.85)':'rgba(165,205,192,.32)';ctx.lineWidth=.85;ctx.beginPath();ctx.arc(p.x,p.y,r+6+(Math.sin(t*1.6+i)*1.7),0,TAU);ctx.stroke();ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=12;ctx.beginPath();ctx.arc(p.x,p.y,r,0,TAU);ctx.fill();ctx.shadowBlur=0;
 ctx.fillStyle=chosen?'#e7faee':'#a7bdc6';ctx.font=`${chosen?'600':'400'} ${w<400?10:11}px ui-monospace,monospace`;ctx.fillText(n.name+'  ·  MODEL',p.x+10,p.y-9);this.hit.push({node:n,...p})}
 ctx.font='10px ui-monospace,monospace';ctx.fillStyle='rgba(132,202,202,.65)';ctx.fillText('SHELL '+(this.level+1)+' · '+this.stars.length+' CATALOG DIRECTIONS · ARTISTIC DISTANCES',17,15);
 }
}
const api={SkyEngine,vec,rotate,project,DEST};if(typeof module!=='undefined'&&module.exports)module.exports=api;global.CelestialShells=api;
})(typeof window!=='undefined'?window:globalThis);
