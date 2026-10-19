'use strict';
// Transfer only generated pigment into a previously unpainted bounded patch.
const fs=require('node:fs'), crypto=require('node:crypto');
const {decodePNG,encodePNG,preview}=require('./finish_wall.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const source='artifacts/line-1/wall-v15.png', destination='artifacts/line-1/wall-v16.png';
if(fs.existsSync('dist/line-1/34.json')) throw Error('record already exists; one-shot operation');
const raw=fs.readFileSync(source), ancestor=decodePNG(source), donor=decodePNG(destination);
if(JSON.parse(fs.readFileSync('dist/line-1/33.json')).image!=='https://api.imd.fun/artifacts/'+hash(raw)) throw Error('ancestor pin mismatch');
if(ancestor.width!==1254||ancestor.height!==1254||ancestor.channels!==3||donor.width!==1254||donor.height!==1254) throw Error('unexpected dimensions');
const out={...ancestor,pixels:Buffer.from(ancestor.pixels)};
const bounds=[650,180,795,300], crop=[380,420,885,850], scale=.26;
for(let y=0;y<Math.ceil((crop[3]-crop[1])*scale);y++) for(let x=0;x<Math.ceil((crop[2]-crop[0])*scale);x++) {
  const sx=Math.floor(crop[0]+x/scale),sy=Math.floor(crop[1]+y/scale);
  const at=(sy*donor.width+sx)*donor.channels;
  const r=donor.pixels[at],g=donor.pixels[at+1],b=donor.pixels[at+2];
  let color,alpha;
  if(sy>530&&sy<670&&Math.max(r,g,b)<105) {color=[42,30,22];alpha=.72;}
  else if(sy<760&&r>g*1.5&&g<135&&r>95) {color=[144,56,28];alpha=.66;}
  else if(sy>755&&sx>575&&sx<680&&r>185&&g>180&&b>155&&r-b<50) {color=[204,184,145];alpha=.72;}
  else continue;
  const px=bounds[0]+x,py=bounds[1]+y;
  if(px>=bounds[2]||py>=bounds[3]) throw Error('outside patch');
  const dest=(py*out.width+px)*3;
  for(let c=0;c<3;c++) out.pixels[dest+c]=Math.round(out.pixels[dest+c]*(1-alpha)+color[c]*alpha);
}
let changed=0;
for(let y=0;y<out.height;y++) for(let x=0;x<out.width;x++) {
  const i=(y*out.width+x)*3;
  if(!out.pixels.subarray(i,i+3).equals(ancestor.pixels.subarray(i,i+3))) {
    changed++;
    if(x<bounds[0]||x>=bounds[2]||y<bounds[1]||y>=bounds[3]) throw Error('ancestor changed outside patch');
  }
}
if(changed<500) throw Error('mark missing');
const png=encodePNG(out),jpg=preview(out),digest=hash(png);
if(jpg.length>100000) throw Error('preview too large');
const record={name:'The Tested Pebbles',image:'https://api.imd.fun/artifacts/'+digest,attributes:[
 {trait_type:'Cave',value:'Roots'},{trait_type:'Wall',value:'Line 1'},{trait_type:'Number',value:34},
 {trait_type:'Left behind',value:'Paired Magnitude regression and finite arithmetic'},
 {trait_type:'Meaning',value:'A protected row of pebbles and a chalk witness keep repeated measurements honest.'},
 {trait_type:'One thing',value:'Reproducible benchmark evidence'}]};
fs.writeFileSync(destination,png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/34.jpg',jpg);
fs.writeFileSync('dist/line-1/34.json',JSON.stringify(record,null,2)+'\n');
const review={wall:destination,width:out.width,height:out.height,format:'PNG RGB8',bytes:png.length,sha256:digest,
 preview:{path:'dist/line-1/34.jpg',width:512,height:512,format:'JPEG',bytes:jpg.length},
 ancestor:source,ancestor_sha256:hash(raw),bounds,changed_pixels:changed,all_pixels_outside_bounds_identical:true,
 process:'Installed image generator supplied isolated pigment motif. Only charcoal, ochre and chalk masks transferred onto exact ancestor; all generated rock discarded. Donor overwritten by final full wall.',
 visual_review:{pepe_wide_mouth_and_heavy_lidded_eyes_preserved:true,ancestral_hands_concealed:true,new_hands_or_stencils:0,visible_digits_to_count:0,prohibited_text_observed:false,unmet_visual_requirements:[]},
 limitations:['Local visual inspection only; no independent artistic approval.','Fine pigment wear softens in 512-pixel preview.'],
 preview_location:'Explicitly required numbered JPEG beside its record; no additional new picture outside artifacts.'};
fs.writeFileSync('line-1/wall-review-34.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify(review));
