(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([[88],{JRJP:function(e,t,n){(function(e){e(n("VrN/"))})((function(e){"use strict";e.defineMode("crystal",(function(e){function t(e,t){return new RegExp((t?"":"^")+"(?:"+e.join("|")+")"+(t?"$":"\\b"))}function n(e,t,n){return n.tokenize.push(e),e(t,n)}var r=/^(?:[-+/%|&^]|\*\*?|[<>]{2})/,a=/^(?:[=!]~|===|<=>|[<>=!]=?|[|&]{2}|~)/,u=/^(?:\[\][?=]?)/,i=/^(?:\.(?:\.{2})?|->|[?:])/,o=/^[a-z_\u009F-\uFFFF][a-zA-Z0-9_\u009F-\uFFFF]*/,c=/^[A-Z_\u009F-\uFFFF][a-zA-Z0-9_\u009F-\uFFFF]*/,s=t(["abstract","alias","as","asm","begin","break","case","class","def","do","else","elsif","end","ensure","enum","extend","for","fun","if","include","instance_sizeof","lib","macro","module","next","of","out","pointerof","private","protected","rescue","return","require","select","sizeof","struct","super","then","type","typeof","uninitialized","union","unless","until","when","while","with","yield","__DIR__","__END_LINE__","__FILE__","__LINE__"]),f=t(["true","false","nil","self"]),l=["def","fun","macro","class","module","struct","lib","enum","union","do","for"],m=t(l),h=["if","unless","case","while","until","begin","then"],p=t(h),d=["end","else","elsif","rescue","ensure"],k=t(d),F=["\\)","\\}","\\]"],z=new RegExp("^(?:"+F.join("|")+")$"),_={def:y,fun:y,macro:I,class:v,module:v,struct:v,lib:v,enum:v,union:v},b={"[":"]","{":"}","(":")","<":">"};function w(e,t){if(e.eatSpace())return null;if("\\"!=t.lastToken&&e.match("{%",!1))return n(x("%","%"),e,t);if("\\"!=t.lastToken&&e.match("{{",!1))return n(x("{","}"),e,t);if("#"==e.peek())return e.skipToEnd(),"comment";var l;if(e.match(o))return e.eat(/[?!]/),l=e.current(),e.eat(":")?"atom":"."==t.lastToken?"property":s.test(l)?(m.test(l)?"fun"==l&&t.blocks.indexOf("lib")>=0||"def"==l&&"abstract"==t.lastToken||(t.blocks.push(l),t.currentIndent+=1):"operator"!=t.lastStyle&&t.lastStyle||!p.test(l)?"end"==l&&(t.blocks.pop(),t.currentIndent-=1):(t.blocks.push(l),t.currentIndent+=1),_.hasOwnProperty(l)&&t.tokenize.push(_[l]),"keyword"):f.test(l)?"atom":"variable";if(e.eat("@"))return"["==e.peek()?n(g("[","]","meta"),e,t):(e.eat("@"),e.match(o)||e.match(c),"variable-2");if(e.match(c))return"tag";if(e.eat(":"))return e.eat('"')?n(S('"',"atom",!1),e,t):e.match(o)||e.match(c)||e.match(r)||e.match(a)||e.match(u)?"atom":(e.eat(":"),"operator");if(e.eat('"'))return n(S('"',"string",!0),e,t);if("%"==e.peek()){var h,d="string",k=!0;if(e.match("%r"))d="string-2",h=e.next();else if(e.match("%w"))k=!1,h=e.next();else if(e.match("%q"))k=!1,h=e.next();else if(h=e.match(/^%([^\w\s=])/))h=h[1];else{if(e.match(/^%[a-zA-Z_\u009F-\uFFFF][\w\u009F-\uFFFF]*/))return"meta";if(e.eat("%"))return"operator"}return b.hasOwnProperty(h)&&(h=b[h]),n(S(h,d,k),e,t)}return(l=e.match(/^<<-('?)([A-Z]\w*)\1/))?n(E(l[2],!l[1]),e,t):e.eat("'")?(e.match(/^(?:[^']|\\(?:[befnrtv0'"]|[0-7]{3}|u(?:[0-9a-fA-F]{4}|\{[0-9a-fA-F]{1,6}\})))/),e.eat("'"),"atom"):e.eat("0")?(e.eat("x")?e.match(/^[0-9a-fA-F_]+/):e.eat("o")?e.match(/^[0-7_]+/):e.eat("b")&&e.match(/^[01_]+/),"number"):e.eat(/^\d/)?(e.match(/^[\d_]*(?:\.[\d_]+)?(?:[eE][+-]?\d+)?/),"number"):e.match(r)?(e.eat("="),"operator"):e.match(a)||e.match(i)?"operator":(l=e.match(/[({[]/,!1))?(l=l[0],n(g(l,b[l],null),e,t)):e.eat("\\")?(e.next(),"meta"):(e.next(),null)}function g(e,t,n,r){return function(a,u){if(!r&&a.match(e))return u.tokenize[u.tokenize.length-1]=g(e,t,n,!0),u.currentIndent+=1,n;var i=w(a,u);return a.current()===t&&(u.tokenize.pop(),u.currentIndent-=1,i=n),i}}function x(e,t,n){return function(r,a){return!n&&r.match("{"+e)?(a.currentIndent+=1,a.tokenize[a.tokenize.length-1]=x(e,t,!0),"meta"):r.match(t+"}")?(a.currentIndent-=1,a.tokenize.pop(),"meta"):w(r,a)}}function I(e,t){if(e.eatSpace())return null;var n;if(n=e.match(o)){if("def"==n)return"keyword";e.eat(/[?!]/)}return t.tokenize.pop(),"def"}function y(e,t){return e.eatSpace()?null:(e.match(o)?e.eat(/[!?]/):e.match(r)||e.match(a)||e.match(u),t.tokenize.pop(),"def")}function v(e,t){return e.eatSpace()?null:(e.match(c),t.tokenize.pop(),"def")}function S(e,t,n){return function(r,a){var u=!1;while(r.peek())if(u)r.next(),u=!1;else{if(r.match("{%",!1))return a.tokenize.push(x("%","%")),t;if(r.match("{{",!1))return a.tokenize.push(x("{","}")),t;if(n&&r.match("#{",!1))return a.tokenize.push(g("#{","}","meta")),t;var i=r.next();if(i==e)return a.tokenize.pop(),t;u=n&&"\\"==i}return t}}function E(e,t){return function(n,r){if(n.sol()&&(n.eatSpace(),n.match(e)))return r.tokenize.pop(),"string";var a=!1;while(n.peek())if(a)n.next(),a=!1;else{if(n.match("{%",!1))return r.tokenize.push(x("%","%")),"string";if(n.match("{{",!1))return r.tokenize.push(x("{","}")),"string";if(t&&n.match("#{",!1))return r.tokenize.push(g("#{","}","meta")),"string";a=t&&"\\"==n.next()}return"string"}}return{startState:function(){return{tokenize:[w],currentIndent:0,lastToken:null,lastStyle:null,blocks:[]}},token:function(e,t){var n=t.tokenize[t.tokenize.length-1](e,t),r=e.current();return n&&"comment"!=n&&(t.lastToken=r,t.lastStyle=n),n},indent:function(t,n){return n=n.replace(/^\s*(?:\{%)?\s*|\s*(?:%\})?\s*$/g,""),k.test(n)||z.test(n)?e.indentUnit*(t.currentIndent-1):e.indentUnit*t.currentIndent},fold:"indent",electricInput:t(F.concat(d),!0),lineComment:"#"}})),e.defineMIME("text/x-crystal","crystal")}))}}]);