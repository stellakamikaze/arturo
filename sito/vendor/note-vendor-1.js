/*! Barretta delle note di Arturo: react@18.3.1 e react-dom@18.3.1 (MIT, Meta Platforms), scheduler@0.23.2 (MIT),
    agentation@3.0.2 (PolyForm Shield 1.0.0, https://polyformproject.org/licenses/shield/1.0.0/).
    Bundle ESM costruito il 16/10/2026 con esbuild 0.25.10 da `import * as R from "react"; import * as RD from
    "react-dom/client"; import * as AG from "agentation"; export { R, RD, AG };`. Prima arrivavano da esm.sh. */
var Lm=Object.create;var Ga=Object.defineProperty;var Im=Object.getOwnPropertyDescriptor;var Nm=Object.getOwnPropertyNames;var $m=Object.getPrototypeOf,Rm=Object.prototype.hasOwnProperty;var vo=(e,t)=>()=>(t||e((t={exports:{}}).exports,t),t.exports),Pm=(e,t)=>{for(var n in t)Ga(e,n,{get:t[n],enumerable:!0})},Tm=(e,t,n,o)=>{if(t&&typeof t=="object"||typeof t=="function")for(let r of Nm(t))!Rm.call(e,r)&&r!==n&&Ga(e,r,{get:()=>t[r],enumerable:!(o=Im(t,r))||o.enumerable});return e};var _t=(e,t,n)=>(n=e!=null?Lm($m(e)):{},Tm(t||!e||!e.__esModule?Ga(n,"default",{value:e,enumerable:!0}):n,e));var S_=vo(Ae=>{"use strict";var Ol=Symbol.for("react.element"),Dm=Symbol.for("react.portal"),Bm=Symbol.for("react.fragment"),zm=Symbol.for("react.strict_mode"),Om=Symbol.for("react.profiler"),Am=Symbol.for("react.provider"),Wm=Symbol.for("react.context"),Fm=Symbol.for("react.forward_ref"),jm=Symbol.for("react.suspense"),Hm=Symbol.for("react.memo"),Um=Symbol.for("react.lazy"),h_=Symbol.iterator;function Ym(e){return e===null||typeof e!="object"?null:(e=h_&&e[h_]||e["@@iterator"],typeof e=="function"?e:null)}var g_={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},y_=Object.assign,x_={};function jr(e,t,n){this.props=e,this.context=t,this.refs=x_,this.updater=n||g_}jr.prototype.isReactComponent={};jr.prototype.setState=function(e,t){if(typeof e!="object"&&typeof e!="function"&&e!=null)throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,e,t,"setState")};jr.prototype.forceUpdate=function(e){this.updater.enqueueForceUpdate(this,e,"forceUpdate")};function v_(){}v_.prototype=jr.prototype;function Ja(e,t,n){this.props=e,this.context=t,this.refs=x_,this.updater=n||g_}var ec=Ja.prototype=new v_;ec.constructor=Ja;y_(ec,jr.prototype);ec.isPureReactComponent=!0;var p_=Array.isArray,w_=Object.prototype.hasOwnProperty,tc={current:null},b_={key:!0,ref:!0,__self:!0,__source:!0};function k_(e,t,n){var o,r={},l=null,i=null;if(t!=null)for(o in t.ref!==void 0&&(i=t.ref),t.key!==void 0&&(l=""+t.key),t)w_.call(t,o)&&!b_.hasOwnProperty(o)&&(r[o]=t[o]);var s=arguments.length-2;if(s===1)r.children=n;else if(1<s){for(var a=Array(s),m=0;m<s;m++)a[m]=arguments[m+2];r.children=a}if(e&&e.defaultProps)for(o in s=e.defaultProps,s)r[o]===void 0&&(r[o]=s[o]);return{$$typeof:Ol,type:e,key:l,ref:i,props:r,_owner:tc.current}}function Xm(e,t){return{$$typeof:Ol,type:e.type,key:t,ref:e.ref,props:e.props,_owner:e._owner}}function nc(e){return typeof e=="object"&&e!==null&&e.$$typeof===Ol}function Qm(e){var t={"=":"=0",":":"=2"};return"$"+e.replace(/[=:]/g,function(n){return t[n]})}var m_=/\/+/g;function Za(e,t){return typeof e=="object"&&e!==null&&e.key!=null?Qm(""+e.key):t.toString(36)}function Zi(e,t,n,o,r){var l=typeof e;(l==="undefined"||l==="boolean")&&(e=null);var i=!1;if(e===null)i=!0;else switch(l){case"string":case"number":i=!0;break;case"object":switch(e.$$typeof){case Ol:case Dm:i=!0}}if(i)return i=e,r=r(i),e=o===""?"."+Za(i,0):o,p_(r)?(n="",e!=null&&(n=e.replace(m_,"$&/")+"/"),Zi(r,t,n,"",function(m){return m})):r!=null&&(nc(r)&&(r=Xm(r,n+(!r.key||i&&i.key===r.key?"":(""+r.key).replace(m_,"$&/")+"/")+e)),t.push(r)),1;if(i=0,o=o===""?".":o+":",p_(e))for(var s=0;s<e.length;s++){l=e[s];var a=o+Za(l,s);i+=Zi(l,t,n,a,r)}else if(a=Ym(e),typeof a=="function")for(e=a.call(e),s=0;!(l=e.next()).done;)l=l.value,a=o+Za(l,s++),i+=Zi(l,t,n,a,r);else if(l==="object")throw t=String(e),Error("Objects are not valid as a React child (found: "+(t==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":t)+"). If you meant to render a collection of children, use an array instead.");return i}function Gi(e,t,n){if(e==null)return e;var o=[],r=0;return Zi(e,o,"","",function(l){return t.call(n,l,r++)}),o}function Vm(e){if(e._status===-1){var t=e._result;t=t(),t.then(function(n){(e._status===0||e._status===-1)&&(e._status=1,e._result=n)},function(n){(e._status===0||e._status===-1)&&(e._status=2,e._result=n)}),e._status===-1&&(e._status=0,e._result=t)}if(e._status===1)return e._result.default;throw e._result}var nn={current:null},Ji={transition:null},Km={ReactCurrentDispatcher:nn,ReactCurrentBatchConfig:Ji,ReactCurrentOwner:tc};function C_(){throw Error("act(...) is not supported in production builds of React.")}Ae.Children={map:Gi,forEach:function(e,t,n){Gi(e,function(){t.apply(this,arguments)},n)},count:function(e){var t=0;return Gi(e,function(){t++}),t},toArray:function(e){return Gi(e,function(t){return t})||[]},only:function(e){if(!nc(e))throw Error("React.Children.only expected to receive a single React element child.");return e}};Ae.Component=jr;Ae.Fragment=Bm;Ae.Profiler=Om;Ae.PureComponent=Ja;Ae.StrictMode=zm;Ae.Suspense=jm;Ae.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=Km;Ae.act=C_;Ae.cloneElement=function(e,t,n){if(e==null)throw Error("React.cloneElement(...): The argument must be a React element, but you passed "+e+".");var o=y_({},e.props),r=e.key,l=e.ref,i=e._owner;if(t!=null){if(t.ref!==void 0&&(l=t.ref,i=tc.current),t.key!==void 0&&(r=""+t.key),e.type&&e.type.defaultProps)var s=e.type.defaultProps;for(a in t)w_.call(t,a)&&!b_.hasOwnProperty(a)&&(o[a]=t[a]===void 0&&s!==void 0?s[a]:t[a])}var a=arguments.length-2;if(a===1)o.children=n;else if(1<a){s=Array(a);for(var m=0;m<a;m++)s[m]=arguments[m+2];o.children=s}return{$$typeof:Ol,type:e.type,key:r,ref:l,props:o,_owner:i}};Ae.createContext=function(e){return e={$$typeof:Wm,_currentValue:e,_currentValue2:e,_threadCount:0,Provider:null,Consumer:null,_defaultValue:null,_globalName:null},e.Provider={$$typeof:Am,_context:e},e.Consumer=e};Ae.createElement=k_;Ae.createFactory=function(e){var t=k_.bind(null,e);return t.type=e,t};Ae.createRef=function(){return{current:null}};Ae.forwardRef=function(e){return{$$typeof:Fm,render:e}};Ae.isValidElement=nc;Ae.lazy=function(e){return{$$typeof:Um,_payload:{_status:-1,_result:e},_init:Vm}};Ae.memo=function(e,t){return{$$typeof:Hm,type:e,compare:t===void 0?null:t}};Ae.startTransition=function(e){var t=Ji.transition;Ji.transition={};try{e()}finally{Ji.transition=t}};Ae.unstable_act=C_;Ae.useCallback=function(e,t){return nn.current.useCallback(e,t)};Ae.useContext=function(e){return nn.current.useContext(e)};Ae.useDebugValue=function(){};Ae.useDeferredValue=function(e){return nn.current.useDeferredValue(e)};Ae.useEffect=function(e,t){return nn.current.useEffect(e,t)};Ae.useId=function(){return nn.current.useId()};Ae.useImperativeHandle=function(e,t,n){return nn.current.useImperativeHandle(e,t,n)};Ae.useInsertionEffect=function(e,t){return nn.current.useInsertionEffect(e,t)};Ae.useLayoutEffect=function(e,t){return nn.current.useLayoutEffect(e,t)};Ae.useMemo=function(e,t){return nn.current.useMemo(e,t)};Ae.useReducer=function(e,t,n){return nn.current.useReducer(e,t,n)};Ae.useRef=function(e){return nn.current.useRef(e)};Ae.useState=function(e){return nn.current.useState(e)};Ae.useSyncExternalStore=function(e,t,n){return nn.current.useSyncExternalStore(e,t,n)};Ae.useTransition=function(){return nn.current.useTransition()};Ae.version="18.3.1"});var Nn=vo((Bx,M_)=>{"use strict";M_.exports=S_()});var B_=vo(ft=>{"use strict";function ic(e,t){var n=e.length;e.push(t);e:for(;0<n;){var o=n-1>>>1,r=e[o];if(0<es(r,t))e[o]=t,e[n]=r,n=o;else break e}}function Yn(e){return e.length===0?null:e[0]}function ns(e){if(e.length===0)return null;var t=e[0],n=e.pop();if(n!==t){e[0]=n;e:for(var o=0,r=e.length,l=r>>>1;o<l;){var i=2*(o+1)-1,s=e[i],a=i+1,m=e[a];if(0>es(s,n))a<r&&0>es(m,s)?(e[o]=m,e[a]=n,o=a):(e[o]=s,e[i]=n,o=i);else if(a<r&&0>es(m,n))e[o]=m,e[a]=n,o=a;else break e}}return t}function es(e,t){var n=e.sortIndex-t.sortIndex;return n!==0?n:e.id-t.id}typeof performance=="object"&&typeof performance.now=="function"?(E_=performance,ft.unstable_now=function(){return E_.now()}):(oc=Date,L_=oc.now(),ft.unstable_now=function(){return oc.now()-L_});var E_,oc,L_,so=[],Bo=[],qm=1,$n=null,Kt=3,os=!1,_r=!1,Wl=!1,$_=typeof setTimeout=="function"?setTimeout:null,R_=typeof clearTimeout=="function"?clearTimeout:null,I_=typeof setImmediate<"u"?setImmediate:null;typeof navigator<"u"&&navigator.scheduling!==void 0&&navigator.scheduling.isInputPending!==void 0&&navigator.scheduling.isInputPending.bind(navigator.scheduling);function sc(e){for(var t=Yn(Bo);t!==null;){if(t.callback===null)ns(Bo);else if(t.startTime<=e)ns(Bo),t.sortIndex=t.expirationTime,ic(so,t);else break;t=Yn(Bo)}}function ac(e){if(Wl=!1,sc(e),!_r)if(Yn(so)!==null)_r=!0,dc(cc);else{var t=Yn(Bo);t!==null&&uc(ac,t.startTime-e)}}function cc(e,t){_r=!1,Wl&&(Wl=!1,R_(Fl),Fl=-1),os=!0;var n=Kt;try{for(sc(t),$n=Yn(so);$n!==null&&(!($n.expirationTime>t)||e&&!D_());){var o=$n.callback;if(typeof o=="function"){$n.callback=null,Kt=$n.priorityLevel;var r=o($n.expirationTime<=t);t=ft.unstable_now(),typeof r=="function"?$n.callback=r:$n===Yn(so)&&ns(so),sc(t)}else ns(so);$n=Yn(so)}if($n!==null)var l=!0;else{var i=Yn(Bo);i!==null&&uc(ac,i.startTime-t),l=!1}return l}finally{$n=null,Kt=n,os=!1}}var rs=!1,ts=null,Fl=-1,P_=5,T_=-1;function D_(){return!(ft.unstable_now()-T_<P_)}function rc(){if(ts!==null){var e=ft.unstable_now();T_=e;var t=!0;try{t=ts(!0,e)}finally{t?Al():(rs=!1,ts=null)}}else rs=!1}var Al;typeof I_=="function"?Al=function(){I_(rc)}:typeof MessageChannel<"u"?(lc=new MessageChannel,N_=lc.port2,lc.port1.onmessage=rc,Al=function(){N_.postMessage(null)}):Al=function(){$_(rc,0)};var lc,N_;function dc(e){ts=e,rs||(rs=!0,Al())}function uc(e,t){Fl=$_(function(){e(ft.unstable_now())},t)}ft.unstable_IdlePriority=5;ft.unstable_ImmediatePriority=1;ft.unstable_LowPriority=4;ft.unstable_NormalPriority=3;ft.unstable_Profiling=null;ft.unstable_UserBlockingPriority=2;ft.unstable_cancelCallback=function(e){e.callback=null};ft.unstable_continueExecution=function(){_r||os||(_r=!0,dc(cc))};ft.unstable_forceFrameRate=function(e){0>e||125<e?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):P_=0<e?Math.floor(1e3/e):5};ft.unstable_getCurrentPriorityLevel=function(){return Kt};ft.unstable_getFirstCallbackNode=function(){return Yn(so)};ft.unstable_next=function(e){switch(Kt){case 1:case 2:case 3:var t=3;break;default:t=Kt}var n=Kt;Kt=t;try{return e()}finally{Kt=n}};ft.unstable_pauseExecution=function(){};ft.unstable_requestPaint=function(){};ft.unstable_runWithPriority=function(e,t){switch(e){case 1:case 2:case 3:case 4:case 5:break;default:e=3}var n=Kt;Kt=e;try{return t()}finally{Kt=n}};ft.unstable_scheduleCallback=function(e,t,n){var o=ft.unstable_now();switch(typeof n=="object"&&n!==null?(n=n.delay,n=typeof n=="number"&&0<n?o+n:o):n=o,e){case 1:var r=-1;break;case 2:r=250;break;case 5:r=1073741823;break;case 4:r=1e4;break;default:r=5e3}return r=n+r,e={id:qm++,callback:t,priorityLevel:e,startTime:n,expirationTime:r,sortIndex:-1},n>o?(e.sortIndex=n,ic(Bo,e),Yn(so)===null&&e===Yn(Bo)&&(Wl?(R_(Fl),Fl=-1):Wl=!0,uc(ac,n-o))):(e.sortIndex=r,ic(so,e),_r||os||(_r=!0,dc(cc))),e};ft.unstable_shouldYield=D_;ft.unstable_wrapCallback=function(e){var t=Kt;return function(){var n=Kt;Kt=t;try{return e.apply(this,arguments)}finally{Kt=n}}}});var O_=vo((Ox,z_)=>{"use strict";z_.exports=B_()});var Hh=vo(kn=>{"use strict";var Gm=Nn(),wn=O_();function H(e){for(var t="https://reactjs.org/docs/error-decoder.html?invariant="+e,n=1;n<arguments.length;n++)t+="&args[]="+encodeURIComponent(arguments[n]);return"Minified React error #"+e+"; visit "+t+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}var Y0=new Set,ci={};function Sr(e,t){cl(e,t),cl(e+"Capture",t)}function cl(e,t){for(ci[e]=t,e=0;e<t.length;e++)Y0.add(t[e])}var Mo=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),Tc=Object.prototype.hasOwnProperty,Zm=/^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/,A_={},W_={};function Jm(e){return Tc.call(W_,e)?!0:Tc.call(A_,e)?!1:Zm.test(e)?W_[e]=!0:(A_[e]=!0,!1)}function e1(e,t,n,o){if(n!==null&&n.type===0)return!1;switch(typeof t){case"function":case"symbol":return!0;case"boolean":return o?!1:n!==null?!n.acceptsBooleans:(e=e.toLowerCase().slice(0,5),e!=="data-"&&e!=="aria-");default:return!1}}function t1(e,t,n,o){if(t===null||typeof t>"u"||e1(e,t,n,o))return!0;if(o)return!1;if(n!==null)switch(n.type){case 3:return!t;case 4:return t===!1;case 5:return isNaN(t);case 6:return isNaN(t)||1>t}return!1}function ln(e,t,n,o,r,l,i){this.acceptsBooleans=t===2||t===3||t===4,this.attributeName=o,this.attributeNamespace=r,this.mustUseProperty=n,this.propertyName=e,this.type=t,this.sanitizeURL=l,this.removeEmptyString=i}var Qt={};"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e){Qt[e]=new ln(e,0,!1,e,null,!1,!1)});[["acceptCharset","accept-charset"],["className","class"],["htmlFor","for"],["httpEquiv","http-equiv"]].forEach(function(e){var t=e[0];Qt[t]=new ln(t,1,!1,e[1],null,!1,!1)});["contentEditable","draggable","spellCheck","value"].forEach(function(e){Qt[e]=new ln(e,2,!1,e.toLowerCase(),null,!1,!1)});["autoReverse","externalResourcesRequired","focusable","preserveAlpha"].forEach(function(e){Qt[e]=new ln(e,2,!1,e,null,!1,!1)});"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e){Qt[e]=new ln(e,3,!1,e.toLowerCase(),null,!1,!1)});["checked","multiple","muted","selected"].forEach(function(e){Qt[e]=new ln(e,3,!0,e,null,!1,!1)});["capture","download"].forEach(function(e){Qt[e]=new ln(e,4,!1,e,null,!1,!1)});["cols","rows","size","span"].forEach(function(e){Qt[e]=new ln(e,6,!1,e,null,!1,!1)});["rowSpan","start"].forEach(function(e){Qt[e]=new ln(e,5,!1,e.toLowerCase(),null,!1,!1)});var Md=/[\-:]([a-z])/g;function Ed(e){return e[1].toUpperCase()}"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e){var t=e.replace(Md,Ed);Qt[t]=new ln(t,1,!1,e,null,!1,!1)});"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e){var t=e.replace(Md,Ed);Qt[t]=new ln(t,1,!1,e,"http://www.w3.org/1999/xlink",!1,!1)});["xml:base","xml:lang","xml:space"].forEach(function(e){var t=e.replace(Md,Ed);Qt[t]=new ln(t,1,!1,e,"http://www.w3.org/XML/1998/namespace",!1,!1)});["tabIndex","crossOrigin"].forEach(function(e){Qt[e]=new ln(e,1,!1,e.toLowerCase(),null,!1,!1)});Qt.xlinkHref=new ln("xlinkHref",1,!1,"xlink:href","http://www.w3.org/1999/xlink",!0,!1);["src","href","action","formAction"].forEach(function(e){Qt[e]=new ln(e,1,!1,e.toLowerCase(),null,!0,!0)});function Ld(e,t,n,o){var r=Qt.hasOwnProperty(t)?Qt[t]:null;(r!==null?r.type!==0:o||!(2<t.length)||t[0]!=="o"&&t[0]!=="O"||t[1]!=="n"&&t[1]!=="N")&&(t1(t,n,r,o)&&(n=null),o||r===null?Jm(t)&&(n===null?e.removeAttribute(t):e.setAttribute(t,""+n)):r.mustUseProperty?e[r.propertyName]=n===null?r.type===3?!1:"":n:(t=r.attributeName,o=r.attributeNamespace,n===null?e.removeAttribute(t):(r=r.type,n=r===3||r===4&&n===!0?"":""+n,o?e.setAttributeNS(o,t,n):e.setAttribute(t,n))))}var No=Gm.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED,ls=Symbol.for("react.element"),Yr=Symbol.for("react.portal"),Xr=Symbol.for("react.fragment"),Id=Symbol.for("react.strict_mode"),Dc=Symbol.for("react.profiler"),X0=Symbol.for("react.provider"),Q0=Symbol.for("react.context"),Nd=Symbol.for("react.forward_ref"),Bc=Symbol.for("react.suspense"),zc=Symbol.for("react.suspense_list"),$d=Symbol.for("react.memo"),Oo=Symbol.for("react.lazy");Symbol.for("react.scope");Symbol.for("react.debug_trace_mode");var V0=Symbol.for("react.offscreen");Symbol.for("react.legacy_hidden");Symbol.for("react.cache");Symbol.for("react.tracing_marker");var F_=Symbol.iterator;function jl(e){return e===null||typeof e!="object"?null:(e=F_&&e[F_]||e["@@iterator"],typeof e=="function"?e:null)}var kt=Object.assign,_c;function ql(e){if(_c===void 0)try{throw Error()}catch(n){var t=n.stack.trim().match(/\n( *(at )?)/);_c=t&&t[1]||""}return`
`+_c+e}var fc=!1;function hc(e,t){if(!e||fc)return"";fc=!0;var n=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{if(t)if(t=function(){throw Error()},Object.defineProperty(t.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(t,[])}catch(m){var o=m}Reflect.construct(e,[],t)}else{try{t.call()}catch(m){o=m}e.call(t.prototype)}else{try{throw Error()}catch(m){o=m}e()}}catch(m){if(m&&o&&typeof m.stack=="string"){for(var r=m.stack.split(`
`),l=o.stack.split(`
`),i=r.length-1,s=l.length-1;1<=i&&0<=s&&r[i]!==l[s];)s--;for(;1<=i&&0<=s;i--,s--)if(r[i]!==l[s]){if(i!==1||s!==1)do if(i--,s--,0>s||r[i]!==l[s]){var a=`
`+r[i].replace(" at new "," at ");return e.displayName&&a.includes("<anonymous>")&&(a=a.replace("<anonymous>",e.displayName)),a}while(1<=i&&0<=s);break}}}finally{fc=!1,Error.prepareStackTrace=n}return(e=e?e.displayName||e.name:"")?ql(e):""}function n1(e){switch(e.tag){case 5:return ql(e.type);case 16:return ql("Lazy");case 13:return ql("Suspense");case 19:return ql("SuspenseList");case 0:case 2:case 15:return e=hc(e.type,!1),e;case 11:return e=hc(e.type.render,!1),e;case 1:return e=hc(e.type,!0),e;default:return""}}function Oc(e){if(e==null)return null;if(typeof e=="function")return e.displayName||e.name||null;if(typeof e=="string")return e;switch(e){case Xr:return"Fragment";case Yr:return"Portal";case Dc:return"Profiler";case Id:return"StrictMode";case Bc:return"Suspense";case zc:return"SuspenseList"}if(typeof e=="object")switch(e.$$typeof){case Q0:return(e.displayName||"Context")+".Consumer";case X0:return(e._context.displayName||"Context")+".Provider";case Nd:var t=e.render;return e=e.displayName,e||(e=t.displayName||t.name||"",e=e!==""?"ForwardRef("+e+")":"ForwardRef"),e;case $d:return t=e.displayName||null,t!==null?t:Oc(e.type)||"Memo";case Oo:t=e._payload,e=e._init;try{return Oc(e(t))}catch{}}return null}function o1(e){var t=e.type;switch(e.tag){case 24:return"Cache";case 9:return(t.displayName||"Context")+".Consumer";case 10:return(t._context.displayName||"Context")+".Provider";case 18:return"DehydratedFragment";case 11:return e=t.render,e=e.displayName||e.name||"",t.displayName||(e!==""?"ForwardRef("+e+")":"ForwardRef");case 7:return"Fragment";case 5:return t;case 4:return"Portal";case 3:return"Root";case 6:return"Text";case 16:return Oc(t);case 8:return t===Id?"StrictMode":"Mode";case 22:return"Offscreen";case 12:return"Profiler";case 21:return"Scope";case 13:return"Suspense";case 19:return"SuspenseList";case 25:return"TracingMarker";case 1:case 0:case 17:case 2:case 14:case 15:if(typeof t=="function")return t.displayName||t.name||null;if(typeof t=="string")return t}return null}function Zo(e){switch(typeof e){case"boolean":case"number":case"string":case"undefined":return e;case"object":return e;default:return""}}function K0(e){var t=e.type;return(e=e.nodeName)&&e.toLowerCase()==="input"&&(t==="checkbox"||t==="radio")}function r1(e){var t=K0(e)?"checked":"value",n=Object.getOwnPropertyDescriptor(e.constructor.prototype,t),o=""+e[t];if(!e.hasOwnProperty(t)&&typeof n<"u"&&typeof n.get=="function"&&typeof n.set=="function"){var r=n.get,l=n.set;return Object.defineProperty(e,t,{configurable:!0,get:function(){return r.call(this)},set:function(i){o=""+i,l.call(this,i)}}),Object.defineProperty(e,t,{enumerable:n.enumerable}),{getValue:function(){return o},setValue:function(i){o=""+i},stopTracking:function(){e._valueTracker=null,delete e[t]}}}}function is(e){e._valueTracker||(e._valueTracker=r1(e))}function q0(e){if(!e)return!1;var t=e._valueTracker;if(!t)return!0;var n=t.getValue(),o="";return e&&(o=K0(e)?e.checked?"true":"false":e.value),e=o,e!==n?(t.setValue(e),!0):!1}function Ts(e){if(e=e||(typeof document<"u"?document:void 0),typeof e>"u")return null;try{return e.activeElement||e.body}catch{return e.body}}function Ac(e,t){var n=t.checked;return kt({},t,{defaultChecked:void 0,defaultValue:void 0,value:void 0,checked:n??e._wrapperState.initialChecked})}function j_(e,t){var n=t.defaultValue==null?"":t.defaultValue,o=t.checked!=null?t.checked:t.defaultChecked;n=Zo(t.value!=null?t.value:n),e._wrapperState={initialChecked:o,initialValue:n,controlled:t.type==="checkbox"||t.type==="radio"?t.checked!=null:t.value!=null}}function G0(e,t){t=t.checked,t!=null&&Ld(e,"checked",t,!1)}function Wc(e,t){G0(e,t);var n=Zo(t.value),o=t.type;if(n!=null)o==="number"?(n===0&&e.value===""||e.value!=n)&&(e.value=""+n):e.value!==""+n&&(e.value=""+n);else if(o==="submit"||o==="reset"){e.removeAttribute("value");return}t.hasOwnProperty("value")?Fc(e,t.type,n):t.hasOwnProperty("defaultValue")&&Fc(e,t.type,Zo(t.defaultValue)),t.checked==null&&t.defaultChecked!=null&&(e.defaultChecked=!!t.defaultChecked)}function H_(e,t,n){if(t.hasOwnProperty("value")||t.hasOwnProperty("defaultValue")){var o=t.type;if(!(o!=="submit"&&o!=="reset"||t.value!==void 0&&t.value!==null))return;t=""+e._wrapperState.initialValue,n||t===e.value||(e.value=t),e.defaultValue=t}n=e.name,n!==""&&(e.name=""),e.defaultChecked=!!e._wrapperState.initialChecked,n!==""&&(e.name=n)}function Fc(e,t,n){(t!=="number"||Ts(e.ownerDocument)!==e)&&(n==null?e.defaultValue=""+e._wrapperState.initialValue:e.defaultValue!==""+n&&(e.defaultValue=""+n))}var Gl=Array.isArray;function ol(e,t,n,o){if(e=e.options,t){t={};for(var r=0;r<n.length;r++)t["$"+n[r]]=!0;for(n=0;n<e.length;n++)r=t.hasOwnProperty("$"+e[n].value),e[n].selected!==r&&(e[n].selected=r),r&&o&&(e[n].defaultSelected=!0)}else{for(n=""+Zo(n),t=null,r=0;r<e.length;r++){if(e[r].value===n){e[r].selected=!0,o&&(e[r].defaultSelected=!0);return}t!==null||e[r].disabled||(t=e[r])}t!==null&&(t.selected=!0)}}function jc(e,t){if(t.dangerouslySetInnerHTML!=null)throw Error(H(91));return kt({},t,{value:void 0,defaultValue:void 0,children:""+e._wrapperState.initialValue})}function U_(e,t){var n=t.value;if(n==null){if(n=t.children,t=t.defaultValue,n!=null){if(t!=null)throw Error(H(92));if(Gl(n)){if(1<n.length)throw Error(H(93));n=n[0]}t=n}t==null&&(t=""),n=t}e._wrapperState={initialValue:Zo(n)}}function Z0(e,t){var n=Zo(t.value),o=Zo(t.defaultValue);n!=null&&(n=""+n,n!==e.value&&(e.value=n),t.defaultValue==null&&e.defaultValue!==n&&(e.defaultValue=n)),o!=null&&(e.defaultValue=""+o)}function Y_(e){var t=e.textContent;t===e._wrapperState.initialValue&&t!==""&&t!==null&&(e.value=t)}function J0(e){switch(e){case"svg":return"http://www.w3.org/2000/svg";case"math":return"http://www.w3.org/1998/Math/MathML";default:return"http://www.w3.org/1999/xhtml"}}function Hc(e,t){return e==null||e==="http://www.w3.org/1999/xhtml"?J0(t):e==="http://www.w3.org/2000/svg"&&t==="foreignObject"?"http://www.w3.org/1999/xhtml":e}var ss,ef=(function(e){return typeof MSApp<"u"&&MSApp.execUnsafeLocalFunction?function(t,n,o,r){MSApp.execUnsafeLocalFunction(function(){return e(t,n,o,r)})}:e})(function(e,t){if(e.namespaceURI!=="http://www.w3.org/2000/svg"||"innerHTML"in e)e.innerHTML=t;else{for(ss=ss||document.createElement("div"),ss.innerHTML="<svg>"+t.valueOf().toString()+"</svg>",t=ss.firstChild;e.firstChild;)e.removeChild(e.firstChild);for(;t.firstChild;)e.appendChild(t.firstChild)}});function di(e,t){if(t){var n=e.firstChild;if(n&&n===e.lastChild&&n.nodeType===3){n.nodeValue=t;return}}e.textContent=t}var ei={animationIterationCount:!0,aspectRatio:!0,borderImageOutset:!0,borderImageSlice:!0,borderImageWidth:!0,boxFlex:!0,boxFlexGroup:!0,boxOrdinalGroup:!0,columnCount:!0,columns:!0,flex:!0,flexGrow:!0,flexPositive:!0,flexShrink:!0,flexNegative:!0,flexOrder:!0,gridArea:!0,gridRow:!0,gridRowEnd:!0,gridRowSpan:!0,gridRowStart:!0,gridColumn:!0,gridColumnEnd:!0,gridColumnSpan:!0,gridColumnStart:!0,fontWeight:!0,lineClamp:!0,lineHeight:!0,opacity:!0,order:!0,orphans:!0,tabSize:!0,widows:!0,zIndex:!0,zoom:!0,fillOpacity:!0,floodOpacity:!0,stopOpacity:!0,strokeDasharray:!0,strokeDashoffset:!0,strokeMiterlimit:!0,strokeOpacity:!0,strokeWidth:!0},l1=["Webkit","ms","Moz","O"];Object.keys(ei).forEach(function(e){l1.forEach(function(t){t=t+e.charAt(0).toUpperCase()+e.substring(1),ei[t]=ei[e]})});function tf(e,t,n){return t==null||typeof t=="boolean"||t===""?"":n||typeof t!="number"||t===0||ei.hasOwnProperty(e)&&ei[e]?(""+t).trim():t+"px"}function nf(e,t){e=e.style;for(var n in t)if(t.hasOwnProperty(n)){var o=n.indexOf("--")===0,r=tf(n,t[n],o);n==="float"&&(n="cssFloat"),o?e.setProperty(n,r):e[n]=r}}var i1=kt({menuitem:!0},{area:!0,base:!0,br:!0,col:!0,embed:!0,hr:!0,img:!0,input:!0,keygen:!0,link:!0,meta:!0,param:!0,source:!0,track:!0,wbr:!0});function Uc(e,t){if(t){if(i1[e]&&(t.children!=null||t.dangerouslySetInnerHTML!=null))throw Error(H(137,e));if(t.dangerouslySetInnerHTML!=null){if(t.children!=null)throw Error(H(60));if(typeof t.dangerouslySetInnerHTML!="object"||!("__html"in t.dangerouslySetInnerHTML))throw Error(H(61))}if(t.style!=null&&typeof t.style!="object")throw Error(H(62))}}function Yc(e,t){if(e.indexOf("-")===-1)return typeof t.is=="string";switch(e){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var Xc=null;function Rd(e){return e=e.target||e.srcElement||window,e.correspondingUseElement&&(e=e.correspondingUseElement),e.nodeType===3?e.parentNode:e}var Qc=null,rl=null,ll=null;function X_(e){if(e=Li(e)){if(typeof Qc!="function")throw Error(H(280));var t=e.stateNode;t&&(t=aa(t),Qc(e.stateNode,e.type,t))}}function of(e){rl?ll?ll.push(e):ll=[e]:rl=e}function rf(){if(rl){var e=rl,t=ll;if(ll=rl=null,X_(e),t)for(e=0;e<t.length;e++)X_(t[e])}}function lf(e,t){return e(t)}function sf(){}var pc=!1;function af(e,t,n){if(pc)return e(t,n);pc=!0;try{return lf(e,t,n)}finally{pc=!1,(rl!==null||ll!==null)&&(sf(),rf())}}function ui(e,t){var n=e.stateNode;if(n===null)return null;var o=aa(n);if(o===null)return null;n=o[t];e:switch(t){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(o=!o.disabled)||(e=e.type,o=!(e==="button"||e==="input"||e==="select"||e==="textarea")),e=!o;break e;default:e=!1}if(e)return null;if(n&&typeof n!="function")throw Error(H(231,t,typeof n));return n}var Vc=!1;if(Mo)try{Hr={},Object.defineProperty(Hr,"passive",{get:function(){Vc=!0}}),window.addEventListener("test",Hr,Hr),window.removeEventListener("test",Hr,Hr)}catch{Vc=!1}var Hr;function s1(e,t,n,o,r,l,i,s,a){var m=Array.prototype.slice.call(arguments,3);try{t.apply(n,m)}catch(p){this.onError(p)}}var ti=!1,Ds=null,Bs=!1,Kc=null,a1={onError:function(e){ti=!0,Ds=e}};function c1(e,t,n,o,r,l,i,s,a){ti=!1,Ds=null,s1.apply(a1,arguments)}function d1(e,t,n,o,r,l,i,s,a){if(c1.apply(this,arguments),ti){if(ti){var m=Ds;ti=!1,Ds=null}else throw Error(H(198));Bs||(Bs=!0,Kc=m)}}function Mr(e){var t=e,n=e;if(e.alternate)for(;t.return;)t=t.return;else{e=t;do t=e,(t.flags&4098)!==0&&(n=t.return),e=t.return;while(e)}return t.tag===3?n:null}function cf(e){if(e.tag===13){var t=e.memoizedState;if(t===null&&(e=e.alternate,e!==null&&(t=e.memoizedState)),t!==null)return t.dehydrated}return null}function Q_(e){if(Mr(e)!==e)throw Error(H(188))}function u1(e){var t=e.alternate;if(!t){if(t=Mr(e),t===null)throw Error(H(188));return t!==e?null:e}for(var n=e,o=t;;){var r=n.return;if(r===null)break;var l=r.alternate;if(l===null){if(o=r.return,o!==null){n=o;continue}break}if(r.child===l.child){for(l=r.child;l;){if(l===n)return Q_(r),e;if(l===o)return Q_(r),t;l=l.sibling}throw Error(H(188))}if(n.return!==o.return)n=r,o=l;else{for(var i=!1,s=r.child;s;){if(s===n){i=!0,n=r,o=l;break}if(s===o){i=!0,o=r,n=l;break}s=s.sibling}if(!i){for(s=l.child;s;){if(s===n){i=!0,n=l,o=r;break}if(s===o){i=!0,o=l,n=r;break}s=s.sibling}if(!i)throw Error(H(189))}}if(n.alternate!==o)throw Error(H(190))}if(n.tag!==3)throw Error(H(188));return n.stateNode.current===n?e:t}function df(e){return e=u1(e),e!==null?uf(e):null}function uf(e){if(e.tag===5||e.tag===6)return e;for(e=e.child;e!==null;){var t=uf(e);if(t!==null)return t;e=e.sibling}return null}var _f=wn.unstable_scheduleCallback,V_=wn.unstable_cancelCallback,_1=wn.unstable_shouldYield,f1=wn.unstable_requestPaint,Rt=wn.unstable_now,h1=wn.unstable_getCurrentPriorityLevel,Pd=wn.unstable_ImmediatePriority,ff=wn.unstable_UserBlockingPriority,zs=wn.unstable_NormalPriority,p1=wn.unstable_LowPriority,hf=wn.unstable_IdlePriority,ra=null,_o=null;function m1(e){if(_o&&typeof _o.onCommitFiberRoot=="function")try{_o.onCommitFiberRoot(ra,e,void 0,(e.current.flags&128)===128)}catch{}}var qn=Math.clz32?Math.clz32:x1,g1=Math.log,y1=Math.LN2;function x1(e){return e>>>=0,e===0?32:31-(g1(e)/y1|0)|0}var as=64,cs=4194304;function Zl(e){switch(e&-e){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return e&4194240;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return e&130023424;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 1073741824;default:return e}}function Os(e,t){var n=e.pendingLanes;if(n===0)return 0;var o=0,r=e.suspendedLanes,l=e.pingedLanes,i=n&268435455;if(i!==0){var s=i&~r;s!==0?o=Zl(s):(l&=i,l!==0&&(o=Zl(l)))}else i=n&~r,i!==0?o=Zl(i):l!==0&&(o=Zl(l));if(o===0)return 0;if(t!==0&&t!==o&&(t&r)===0&&(r=o&-o,l=t&-t,r>=l||r===16&&(l&4194240)!==0))return t;if((o&4)!==0&&(o|=n&16),t=e.entangledLanes,t!==0)for(e=e.entanglements,t&=o;0<t;)n=31-qn(t),r=1<<n,o|=e[n],t&=~r;return o}function v1(e,t){switch(e){case 1:case 2:case 4:return t+250;case 8:case 16:case 32:case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return t+5e3;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return-1;case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function w1(e,t){for(var n=e.suspendedLanes,o=e.pingedLanes,r=e.expirationTimes,l=e.pendingLanes;0<l;){var i=31-qn(l),s=1<<i,a=r[i];a===-1?((s&n)===0||(s&o)!==0)&&(r[i]=v1(s,t)):a<=t&&(e.expiredLanes|=s),l&=~s}}function qc(e){return e=e.pendingLanes&-1073741825,e!==0?e:e&1073741824?1073741824:0}function pf(){var e=as;return as<<=1,(as&4194240)===0&&(as=64),e}function mc(e){for(var t=[],n=0;31>n;n++)t.push(e);return t}function Mi(e,t,n){e.pendingLanes|=t,t!==536870912&&(e.suspendedLanes=0,e.pingedLanes=0),e=e.eventTimes,t=31-qn(t),e[t]=n}function b1(e,t){var n=e.pendingLanes&~t;e.pendingLanes=t,e.suspendedLanes=0,e.pingedLanes=0,e.expiredLanes&=t,e.mutableReadLanes&=t,e.entangledLanes&=t,t=e.entanglements;var o=e.eventTimes;for(e=e.expirationTimes;0<n;){var r=31-qn(n),l=1<<r;t[r]=0,o[r]=-1,e[r]=-1,n&=~l}}function Td(e,t){var n=e.entangledLanes|=t;for(e=e.entanglements;n;){var o=31-qn(n),r=1<<o;r&t|e[o]&t&&(e[o]|=t),n&=~r}}var lt=0;function mf(e){return e&=-e,1<e?4<e?(e&268435455)!==0?16:536870912:4:1}var gf,Dd,yf,xf,vf,Gc=!1,ds=[],Uo=null,Yo=null,Xo=null,_i=new Map,fi=new Map,Wo=[],k1="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");function K_(e,t){switch(e){case"focusin":case"focusout":Uo=null;break;case"dragenter":case"dragleave":Yo=null;break;case"mouseover":case"mouseout":Xo=null;break;case"pointerover":case"pointerout":_i.delete(t.pointerId);break;case"gotpointercapture":case"lostpointercapture":fi.delete(t.pointerId)}}function Hl(e,t,n,o,r,l){return e===null||e.nativeEvent!==l?(e={blockedOn:t,domEventName:n,eventSystemFlags:o,nativeEvent:l,targetContainers:[r]},t!==null&&(t=Li(t),t!==null&&Dd(t)),e):(e.eventSystemFlags|=o,t=e.targetContainers,r!==null&&t.indexOf(r)===-1&&t.push(r),e)}function C1(e,t,n,o,r){switch(t){case"focusin":return Uo=Hl(Uo,e,t,n,o,r),!0;case"dragenter":return Yo=Hl(Yo,e,t,n,o,r),!0;case"mouseover":return Xo=Hl(Xo,e,t,n,o,r),!0;case"pointerover":var l=r.pointerId;return _i.set(l,Hl(_i.get(l)||null,e,t,n,o,r)),!0;case"gotpointercapture":return l=r.pointerId,fi.set(l,Hl(fi.get(l)||null,e,t,n,o,r)),!0}return!1}function wf(e){var t=pr(e.target);if(t!==null){var n=Mr(t);if(n!==null){if(t=n.tag,t===13){if(t=cf(n),t!==null){e.blockedOn=t,vf(e.priority,function(){yf(n)});return}}else if(t===3&&n.stateNode.current.memoizedState.isDehydrated){e.blockedOn=n.tag===3?n.stateNode.containerInfo:null;return}}}e.blockedOn=null}function Cs(e){if(e.blockedOn!==null)return!1;for(var t=e.targetContainers;0<t.length;){var n=Zc(e.domEventName,e.eventSystemFlags,t[0],e.nativeEvent);if(n===null){n=e.nativeEvent;var o=new n.constructor(n.type,n);Xc=o,n.target.dispatchEvent(o),Xc=null}else return t=Li(n),t!==null&&Dd(t),e.blockedOn=n,!1;t.shift()}return!0}function q_(e,t,n){Cs(e)&&n.delete(t)}function S1(){Gc=!1,Uo!==null&&Cs(Uo)&&(Uo=null),Yo!==null&&Cs(Yo)&&(Yo=null),Xo!==null&&Cs(Xo)&&(Xo=null),_i.forEach(q_),fi.forEach(q_)}function Ul(e,t){e.blockedOn===t&&(e.blockedOn=null,Gc||(Gc=!0,wn.unstable_scheduleCallback(wn.unstable_NormalPriority,S1)))}function hi(e){function t(r){return Ul(r,e)}if(0<ds.length){Ul(ds[0],e);for(var n=1;n<ds.length;n++){var o=ds[n];o.blockedOn===e&&(o.blockedOn=null)}}for(Uo!==null&&Ul(Uo,e),Yo!==null&&Ul(Yo,e),Xo!==null&&Ul(Xo,e),_i.forEach(t),fi.forEach(t),n=0;n<Wo.length;n++)o=Wo[n],o.blockedOn===e&&(o.blockedOn=null);for(;0<Wo.length&&(n=Wo[0],n.blockedOn===null);)wf(n),n.blockedOn===null&&Wo.shift()}var il=No.ReactCurrentBatchConfig,As=!0;function M1(e,t,n,o){var r=lt,l=il.transition;il.transition=null;try{lt=1,Bd(e,t,n,o)}finally{lt=r,il.transition=l}}function E1(e,t,n,o){var r=lt,l=il.transition;il.transition=null;try{lt=4,Bd(e,t,n,o)}finally{lt=r,il.transition=l}}function Bd(e,t,n,o){if(As){var r=Zc(e,t,n,o);if(r===null)kc(e,t,o,Ws,n),K_(e,o);else if(C1(r,e,t,n,o))o.stopPropagation();else if(K_(e,o),t&4&&-1<k1.indexOf(e)){for(;r!==null;){var l=Li(r);if(l!==null&&gf(l),l=Zc(e,t,n,o),l===null&&kc(e,t,o,Ws,n),l===r)break;r=l}r!==null&&o.stopPropagation()}else kc(e,t,o,null,n)}}var Ws=null;function Zc(e,t,n,o){if(Ws=null,e=Rd(o),e=pr(e),e!==null)if(t=Mr(e),t===null)e=null;else if(n=t.tag,n===13){if(e=cf(t),e!==null)return e;e=null}else if(n===3){if(t.stateNode.current.memoizedState.isDehydrated)return t.tag===3?t.stateNode.containerInfo:null;e=null}else t!==e&&(e=null);return Ws=e,null}function bf(e){switch(e){case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 1;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"toggle":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 4;case"message":switch(h1()){case Pd:return 1;case ff:return 4;case zs:case p1:return 16;case hf:return 536870912;default:return 16}default:return 16}}var jo=null,zd=null,Ss=null;function kf(){if(Ss)return Ss;var e,t=zd,n=t.length,o,r="value"in jo?jo.value:jo.textContent,l=r.length;for(e=0;e<n&&t[e]===r[e];e++);var i=n-e;for(o=1;o<=i&&t[n-o]===r[l-o];o++);return Ss=r.slice(e,1<o?1-o:void 0)}function Ms(e){var t=e.keyCode;return"charCode"in e?(e=e.charCode,e===0&&t===13&&(e=13)):e=t,e===10&&(e=13),32<=e||e===13?e:0}function us(){return!0}function G_(){return!1}function bn(e){function t(n,o,r,l,i){this._reactName=n,this._targetInst=r,this.type=o,this.nativeEvent=l,this.target=i,this.currentTarget=null;for(var s in e)e.hasOwnProperty(s)&&(n=e[s],this[s]=n?n(l):l[s]);return this.isDefaultPrevented=(l.defaultPrevented!=null?l.defaultPrevented:l.returnValue===!1)?us:G_,this.isPropagationStopped=G_,this}return kt(t.prototype,{preventDefault:function(){this.defaultPrevented=!0;var n=this.nativeEvent;n&&(n.preventDefault?n.preventDefault():typeof n.returnValue!="unknown"&&(n.returnValue=!1),this.isDefaultPrevented=us)},stopPropagation:function(){var n=this.nativeEvent;n&&(n.stopPropagation?n.stopPropagation():typeof n.cancelBubble!="unknown"&&(n.cancelBubble=!0),this.isPropagationStopped=us)},persist:function(){},isPersistent:us}),t}var ml={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(e){return e.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},Od=bn(ml),Ei=kt({},ml,{view:0,detail:0}),L1=bn(Ei),gc,yc,Yl,la=kt({},Ei,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:Ad,button:0,buttons:0,relatedTarget:function(e){return e.relatedTarget===void 0?e.fromElement===e.srcElement?e.toElement:e.fromElement:e.relatedTarget},movementX:function(e){return"movementX"in e?e.movementX:(e!==Yl&&(Yl&&e.type==="mousemove"?(gc=e.screenX-Yl.screenX,yc=e.screenY-Yl.screenY):yc=gc=0,Yl=e),gc)},movementY:function(e){return"movementY"in e?e.movementY:yc}}),Z_=bn(la),I1=kt({},la,{dataTransfer:0}),N1=bn(I1),$1=kt({},Ei,{relatedTarget:0}),xc=bn($1),R1=kt({},ml,{animationName:0,elapsedTime:0,pseudoElement:0}),P1=bn(R1),T1=kt({},ml,{clipboardData:function(e){return"clipboardData"in e?e.clipboardData:window.clipboardData}}),D1=bn(T1),B1=kt({},ml,{data:0}),J_=bn(B1),z1={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},O1={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},A1={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function W1(e){var t=this.nativeEvent;return t.getModifierState?t.getModifierState(e):(e=A1[e])?!!t[e]:!1}function Ad(){return W1}var F1=kt({},Ei,{key:function(e){if(e.key){var t=z1[e.key]||e.key;if(t!=="Unidentified")return t}return e.type==="keypress"?(e=Ms(e),e===13?"Enter":String.fromCharCode(e)):e.type==="keydown"||e.type==="keyup"?O1[e.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:Ad,charCode:function(e){return e.type==="keypress"?Ms(e):0},keyCode:function(e){return e.type==="keydown"||e.type==="keyup"?e.keyCode:0},which:function(e){return e.type==="keypress"?Ms(e):e.type==="keydown"||e.type==="keyup"?e.keyCode:0}}),j1=bn(F1),H1=kt({},la,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),e0=bn(H1),U1=kt({},Ei,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:Ad}),Y1=bn(U1),X1=kt({},ml,{propertyName:0,elapsedTime:0,pseudoElement:0}),Q1=bn(X1),V1=kt({},la,{deltaX:function(e){return"deltaX"in e?e.deltaX:"wheelDeltaX"in e?-e.wheelDeltaX:0},deltaY:function(e){return"deltaY"in e?e.deltaY:"wheelDeltaY"in e?-e.wheelDeltaY:"wheelDelta"in e?-e.wheelDelta:0},deltaZ:0,deltaMode:0}),K1=bn(V1),q1=[9,13,27,32],Wd=Mo&&"CompositionEvent"in window,ni=null;Mo&&"documentMode"in document&&(ni=document.documentMode);var G1=Mo&&"TextEvent"in window&&!ni,Cf=Mo&&(!Wd||ni&&8<ni&&11>=ni),t0=" ",n0=!1;function Sf(e,t){switch(e){case"keyup":return q1.indexOf(t.keyCode)!==-1;case"keydown":return t.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function Mf(e){return e=e.detail,typeof e=="object"&&"data"in e?e.data:null}var Qr=!1;function Z1(e,t){switch(e){case"compositionend":return Mf(t);case"keypress":return t.which!==32?null:(n0=!0,t0);case"textInput":return e=t.data,e===t0&&n0?null:e;default:return null}}function J1(e,t){if(Qr)return e==="compositionend"||!Wd&&Sf(e,t)?(e=kf(),Ss=zd=jo=null,Qr=!1,e):null;switch(e){case"paste":return null;case"keypress":if(!(t.ctrlKey||t.altKey||t.metaKey)||t.ctrlKey&&t.altKey){if(t.char&&1<t.char.length)return t.char;if(t.which)return String.fromCharCode(t.which)}return null;case"compositionend":return Cf&&t.locale!=="ko"?null:t.data;default:return null}}var eg={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function o0(e){var t=e&&e.nodeName&&e.nodeName.toLowerCase();return t==="input"?!!eg[e.type]:t==="textarea"}function Ef(e,t,n,o){of(o),t=Fs(t,"onChange"),0<t.length&&(n=new Od("onChange","change",null,n,o),e.push({event:n,listeners:t}))}var oi=null,pi=null;function tg(e){Of(e,0)}function ia(e){var t=qr(e);if(q0(t))return e}function ng(e,t){if(e==="change")return t}var Lf=!1;Mo&&(Mo?(fs="oninput"in document,fs||(vc=document.createElement("div"),vc.setAttribute("oninput","return;"),fs=typeof vc.oninput=="function"),_s=fs):_s=!1,Lf=_s&&(!document.documentMode||9<document.documentMode));var _s,fs,vc;function r0(){oi&&(oi.detachEvent("onpropertychange",If),pi=oi=null)}function If(e){if(e.propertyName==="value"&&ia(pi)){var t=[];Ef(t,pi,e,Rd(e)),af(tg,t)}}function og(e,t,n){e==="focusin"?(r0(),oi=t,pi=n,oi.attachEvent("onpropertychange",If)):e==="focusout"&&r0()}function rg(e){if(e==="selectionchange"||e==="keyup"||e==="keydown")return ia(pi)}function lg(e,t){if(e==="click")return ia(t)}function ig(e,t){if(e==="input"||e==="change")return ia(t)}function sg(e,t){return e===t&&(e!==0||1/e===1/t)||e!==e&&t!==t}var Zn=typeof Object.is=="function"?Object.is:sg;function mi(e,t){if(Zn(e,t))return!0;if(typeof e!="object"||e===null||typeof t!="object"||t===null)return!1;var n=Object.keys(e),o=Object.keys(t);if(n.length!==o.length)return!1;for(o=0;o<n.length;o++){var r=n[o];if(!Tc.call(t,r)||!Zn(e[r],t[r]))return!1}return!0}function l0(e){for(;e&&e.firstChild;)e=e.firstChild;return e}function i0(e,t){var n=l0(e);e=0;for(var o;n;){if(n.nodeType===3){if(o=e+n.textContent.length,e<=t&&o>=t)return{node:n,offset:t-e};e=o}e:{for(;n;){if(n.nextSibling){n=n.nextSibling;break e}n=n.parentNode}n=void 0}n=l0(n)}}function Nf(e,t){return e&&t?e===t?!0:e&&e.nodeType===3?!1:t&&t.nodeType===3?Nf(e,t.parentNode):"contains"in e?e.contains(t):e.compareDocumentPosition?!!(e.compareDocumentPosition(t)&16):!1:!1}function $f(){for(var e=window,t=Ts();t instanceof e.HTMLIFrameElement;){try{var n=typeof t.contentWindow.location.href=="string"}catch{n=!1}if(n)e=t.contentWindow;else break;t=Ts(e.document)}return t}function Fd(e){var t=e&&e.nodeName&&e.nodeName.toLowerCase();return t&&(t==="input"&&(e.type==="text"||e.type==="search"||e.type==="tel"||e.type==="url"||e.type==="password")||t==="textarea"||e.contentEditable==="true")}function ag(e){var t=$f(),n=e.focusedElem,o=e.selectionRange;if(t!==n&&n&&n.ownerDocument&&Nf(n.ownerDocument.documentElement,n)){if(o!==null&&Fd(n)){if(t=o.start,e=o.end,e===void 0&&(e=t),"selectionStart"in n)n.selectionStart=t,n.selectionEnd=Math.min(e,n.value.length);else if(e=(t=n.ownerDocument||document)&&t.defaultView||window,e.getSelection){e=e.getSelection();var r=n.textContent.length,l=Math.min(o.start,r);o=o.end===void 0?l:Math.min(o.end,r),!e.extend&&l>o&&(r=o,o=l,l=r),r=i0(n,l);var i=i0(n,o);r&&i&&(e.rangeCount!==1||e.anchorNode!==r.node||e.anchorOffset!==r.offset||e.focusNode!==i.node||e.focusOffset!==i.offset)&&(t=t.createRange(),t.setStart(r.node,r.offset),e.removeAllRanges(),l>o?(e.addRange(t),e.extend(i.node,i.offset)):(t.setEnd(i.node,i.offset),e.addRange(t)))}}for(t=[],e=n;e=e.parentNode;)e.nodeType===1&&t.push({element:e,left:e.scrollLeft,top:e.scrollTop});for(typeof n.focus=="function"&&n.focus(),n=0;n<t.length;n++)e=t[n],e.element.scrollLeft=e.left,e.element.scrollTop=e.top}}var cg=Mo&&"documentMode"in document&&11>=document.documentMode,Vr=null,Jc=null,ri=null,ed=!1;function s0(e,t,n){var o=n.window===n?n.document:n.nodeType===9?n:n.ownerDocument;ed||Vr==null||Vr!==Ts(o)||(o=Vr,"selectionStart"in o&&Fd(o)?o={start:o.selectionStart,end:o.selectionEnd}:(o=(o.ownerDocument&&o.ownerDocument.defaultView||window).getSelection(),o={anchorNode:o.anchorNode,anchorOffset:o.anchorOffset,focusNode:o.focusNode,focusOffset:o.focusOffset}),ri&&mi(ri,o)||(ri=o,o=Fs(Jc,"onSelect"),0<o.length&&(t=new Od("onSelect","select",null,t,n),e.push({event:t,listeners:o}),t.target=Vr)))}function hs(e,t){var n={};return n[e.toLowerCase()]=t.toLowerCase(),n["Webkit"+e]="webkit"+t,n["Moz"+e]="moz"+t,n}var Kr={animationend:hs("Animation","AnimationEnd"),animationiteration:hs("Animation","AnimationIteration"),animationstart:hs("Animation","AnimationStart"),transitionend:hs("Transition","TransitionEnd")},wc={},Rf={};Mo&&(Rf=document.createElement("div").style,"AnimationEvent"in window||(delete Kr.animationend.animation,delete Kr.animationiteration.animation,delete Kr.animationstart.animation),"TransitionEvent"in window||delete Kr.transitionend.transition);function sa(e){if(wc[e])return wc[e];if(!Kr[e])return e;var t=Kr[e],n;for(n in t)if(t.hasOwnProperty(n)&&n in Rf)return wc[e]=t[n];return e}var Pf=sa("animationend"),Tf=sa("animationiteration"),Df=sa("animationstart"),Bf=sa("transitionend"),zf=new Map,a0="abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");function er(e,t){zf.set(e,t),Sr(t,[e])}for(ps=0;ps<a0.length;ps++)ms=a0[ps],c0=ms.toLowerCase(),d0=ms[0].toUpperCase()+ms.slice(1),er(c0,"on"+d0);var ms,c0,d0,ps;er(Pf,"onAnimationEnd");er(Tf,"onAnimationIteration");er(Df,"onAnimationStart");er("dblclick","onDoubleClick");er("focusin","onFocus");er("focusout","onBlur");er(Bf,"onTransitionEnd");cl("onMouseEnter",["mouseout","mouseover"]);cl("onMouseLeave",["mouseout","mouseover"]);cl("onPointerEnter",["pointerout","pointerover"]);cl("onPointerLeave",["pointerout","pointerover"]);Sr("onChange","change click focusin focusout input keydown keyup selectionchange".split(" "));Sr("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" "));Sr("onBeforeInput",["compositionend","keypress","textInput","paste"]);Sr("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" "));Sr("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" "));Sr("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var Jl="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),dg=new Set("cancel close invalid load scroll toggle".split(" ").concat(Jl));function u0(e,t,n){var o=e.type||"unknown-event";e.currentTarget=n,d1(o,t,void 0,e),e.currentTarget=null}function Of(e,t){t=(t&4)!==0;for(var n=0;n<e.length;n++){var o=e[n],r=o.event;o=o.listeners;e:{var l=void 0;if(t)for(var i=o.length-1;0<=i;i--){var s=o[i],a=s.instance,m=s.currentTarget;if(s=s.listener,a!==l&&r.isPropagationStopped())break e;u0(r,s,m),l=a}else for(i=0;i<o.length;i++){if(s=o[i],a=s.instance,m=s.currentTarget,s=s.listener,a!==l&&r.isPropagationStopped())break e;u0(r,s,m),l=a}}}if(Bs)throw e=Kc,Bs=!1,Kc=null,e}function pt(e,t){var n=t[ld];n===void 0&&(n=t[ld]=new Set);var o=e+"__bubble";n.has(o)||(Af(t,e,2,!1),n.add(o))}function bc(e,t,n){var o=0;t&&(o|=4),Af(n,e,o,t)}var gs="_reactListening"+Math.random().toString(36).slice(2);function gi(e){if(!e[gs]){e[gs]=!0,Y0.forEach(function(n){n!=="selectionchange"&&(dg.has(n)||bc(n,!1,e),bc(n,!0,e))});var t=e.nodeType===9?e:e.ownerDocument;t===null||t[gs]||(t[gs]=!0,bc("selectionchange",!1,t))}}function Af(e,t,n,o){switch(bf(t)){case 1:var r=M1;break;case 4:r=E1;break;default:r=Bd}n=r.bind(null,t,n,e),r=void 0,!Vc||t!=="touchstart"&&t!=="touchmove"&&t!=="wheel"||(r=!0),o?r!==void 0?e.addEventListener(t,n,{capture:!0,passive:r}):e.addEventListener(t,n,!0):r!==void 0?e.addEventListener(t,n,{passive:r}):e.addEventListener(t,n,!1)}function kc(e,t,n,o,r){var l=o;if((t&1)===0&&(t&2)===0&&o!==null)e:for(;;){if(o===null)return;var i=o.tag;if(i===3||i===4){var s=o.stateNode.containerInfo;if(s===r||s.nodeType===8&&s.parentNode===r)break;if(i===4)for(i=o.return;i!==null;){var a=i.tag;if((a===3||a===4)&&(a=i.stateNode.containerInfo,a===r||a.nodeType===8&&a.parentNode===r))return;i=i.return}for(;s!==null;){if(i=pr(s),i===null)return;if(a=i.tag,a===5||a===6){o=l=i;continue e}s=s.parentNode}}o=o.return}af(function(){var m=l,p=Rd(n),b=[];e:{var y=zf.get(e);if(y!==void 0){var R=Od,C=e;switch(e){case"keypress":if(Ms(n)===0)break e;case"keydown":case"keyup":R=j1;break;case"focusin":C="focus",R=xc;break;case"focusout":C="blur",R=xc;break;case"beforeblur":case"afterblur":R=xc;break;case"click":if(n.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":R=Z_;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":R=N1;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":R=Y1;break;case Pf:case Tf:case Df:R=P1;break;case Bf:R=Q1;break;case"scroll":R=L1;break;case"wheel":R=K1;break;case"copy":case"cut":case"paste":R=D1;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":R=e0}var N=(t&4)!==0,L=!N&&e==="scroll",f=N?y!==null?y+"Capture":null:y;N=[];for(var g=m,w;g!==null;){w=g;var $=w.stateNode;if(w.tag===5&&$!==null&&(w=$,f!==null&&($=ui(g,f),$!=null&&N.push(yi(g,$,w)))),L)break;g=g.return}0<N.length&&(y=new R(y,C,null,n,p),b.push({event:y,listeners:N}))}}if((t&7)===0){e:{if(y=e==="mouseover"||e==="pointerover",R=e==="mouseout"||e==="pointerout",y&&n!==Xc&&(C=n.relatedTarget||n.fromElement)&&(pr(C)||C[Eo]))break e;if((R||y)&&(y=p.window===p?p:(y=p.ownerDocument)?y.defaultView||y.parentWindow:window,R?(C=n.relatedTarget||n.toElement,R=m,C=C?pr(C):null,C!==null&&(L=Mr(C),C!==L||C.tag!==5&&C.tag!==6)&&(C=null)):(R=null,C=m),R!==C)){if(N=Z_,$="onMouseLeave",f="onMouseEnter",g="mouse",(e==="pointerout"||e==="pointerover")&&(N=e0,$="onPointerLeave",f="onPointerEnter",g="pointer"),L=R==null?y:qr(R),w=C==null?y:qr(C),y=new N($,g+"leave",R,n,p),y.target=L,y.relatedTarget=w,$=null,pr(p)===m&&(N=new N(f,g+"enter",C,n,p),N.target=w,N.relatedTarget=L,$=N),L=$,R&&C)t:{for(N=R,f=C,g=0,w=N;w;w=Ur(w))g++;for(w=0,$=f;$;$=Ur($))w++;for(;0<g-w;)N=Ur(N),g--;for(;0<w-g;)f=Ur(f),w--;for(;g--;){if(N===f||f!==null&&N===f.alternate)break t;N=Ur(N),f=Ur(f)}N=null}else N=null;R!==null&&_0(b,y,R,N,!1),C!==null&&L!==null&&_0(b,L,C,N,!0)}}e:{if(y=m?qr(m):window,R=y.nodeName&&y.nodeName.toLowerCase(),R==="select"||R==="input"&&y.type==="file")var U=ng;else if(o0(y))if(Lf)U=ig;else{U=rg;var V=og}else(R=y.nodeName)&&R.toLowerCase()==="input"&&(y.type==="checkbox"||y.type==="radio")&&(U=lg);if(U&&(U=U(e,m))){Ef(b,U,n,p);break e}V&&V(e,y,m),e==="focusout"&&(V=y._wrapperState)&&V.controlled&&y.type==="number"&&Fc(y,"number",y.value)}switch(V=m?qr(m):window,e){case"focusin":(o0(V)||V.contentEditable==="true")&&(Vr=V,Jc=m,ri=null);break;case"focusout":ri=Jc=Vr=null;break;case"mousedown":ed=!0;break;case"contextmenu":case"mouseup":case"dragend":ed=!1,s0(b,n,p);break;case"selectionchange":if(cg)break;case"keydown":case"keyup":s0(b,n,p)}var B;if(Wd)e:{switch(e){case"compositionstart":var q="onCompositionStart";break e;case"compositionend":q="onCompositionEnd";break e;case"compositionupdate":q="onCompositionUpdate";break e}q=void 0}else Qr?Sf(e,n)&&(q="onCompositionEnd"):e==="keydown"&&n.keyCode===229&&(q="onCompositionStart");q&&(Cf&&n.locale!=="ko"&&(Qr||q!=="onCompositionStart"?q==="onCompositionEnd"&&Qr&&(B=kf()):(jo=p,zd="value"in jo?jo.value:jo.textContent,Qr=!0)),V=Fs(m,q),0<V.length&&(q=new J_(q,e,null,n,p),b.push({event:q,listeners:V}),B?q.data=B:(B=Mf(n),B!==null&&(q.data=B)))),(B=G1?Z1(e,n):J1(e,n))&&(m=Fs(m,"onBeforeInput"),0<m.length&&(p=new J_("onBeforeInput","beforeinput",null,n,p),b.push({event:p,listeners:m}),p.data=B))}Of(b,t)})}function yi(e,t,n){return{instance:e,listener:t,currentTarget:n}}function Fs(e,t){for(var n=t+"Capture",o=[];e!==null;){var r=e,l=r.stateNode;r.tag===5&&l!==null&&(r=l,l=ui(e,n),l!=null&&o.unshift(yi(e,l,r)),l=ui(e,t),l!=null&&o.push(yi(e,l,r))),e=e.return}return o}function Ur(e){if(e===null)return null;do e=e.return;while(e&&e.tag!==5);return e||null}function _0(e,t,n,o,r){for(var l=t._reactName,i=[];n!==null&&n!==o;){var s=n,a=s.alternate,m=s.stateNode;if(a!==null&&a===o)break;s.tag===5&&m!==null&&(s=m,r?(a=ui(n,l),a!=null&&i.unshift(yi(n,a,s))):r||(a=ui(n,l),a!=null&&i.push(yi(n,a,s)))),n=n.return}i.length!==0&&e.push({event:t,listeners:i})}var ug=/\r\n?/g,_g=/\u0000|\uFFFD/g;function f0(e){return(typeof e=="string"?e:""+e).replace(ug,`
`).replace(_g,"")}function ys(e,t,n){if(t=f0(t),f0(e)!==t&&n)throw Error(H(425))}function js(){}var td=null,nd=null;function od(e,t){return e==="textarea"||e==="noscript"||typeof t.children=="string"||typeof t.children=="number"||typeof t.dangerouslySetInnerHTML=="object"&&t.dangerouslySetInnerHTML!==null&&t.dangerouslySetInnerHTML.__html!=null}var rd=typeof setTimeout=="function"?setTimeout:void 0,fg=typeof clearTimeout=="function"?clearTimeout:void 0,h0=typeof Promise=="function"?Promise:void 0,hg=typeof queueMicrotask=="function"?queueMicrotask:typeof h0<"u"?function(e){return h0.resolve(null).then(e).catch(pg)}:rd;function pg(e){setTimeout(function(){throw e})}function Cc(e,t){var n=t,o=0;do{var r=n.nextSibling;if(e.removeChild(n),r&&r.nodeType===8)if(n=r.data,n==="/$"){if(o===0){e.removeChild(r),hi(t);return}o--}else n!=="$"&&n!=="$?"&&n!=="$!"||o++;n=r}while(n);hi(t)}function Qo(e){for(;e!=null;e=e.nextSibling){var t=e.nodeType;if(t===1||t===3)break;if(t===8){if(t=e.data,t==="$"||t==="$!"||t==="$?")break;if(t==="/$")return null}}return e}function p0(e){e=e.previousSibling;for(var t=0;e;){if(e.nodeType===8){var n=e.data;if(n==="$"||n==="$!"||n==="$?"){if(t===0)return e;t--}else n==="/$"&&t++}e=e.previousSibling}return null}var gl=Math.random().toString(36).slice(2),uo="__reactFiber$"+gl,xi="__reactProps$"+gl,Eo="__reactContainer$"+gl,ld="__reactEvents$"+gl,mg="__reactListeners$"+gl,gg="__reactHandles$"+gl;function pr(e){var t=e[uo];if(t)return t;for(var n=e.parentNode;n;){if(t=n[Eo]||n[uo]){if(n=t.alternate,t.child!==null||n!==null&&n.child!==null)for(e=p0(e);e!==null;){if(n=e[uo])return n;e=p0(e)}return t}e=n,n=e.parentNode}return null}function Li(e){return e=e[uo]||e[Eo],!e||e.tag!==5&&e.tag!==6&&e.tag!==13&&e.tag!==3?null:e}function qr(e){if(e.tag===5||e.tag===6)return e.stateNode;throw Error(H(33))}function aa(e){return e[xi]||null}var id=[],Gr=-1;function tr(e){return{current:e}}function mt(e){0>Gr||(e.current=id[Gr],id[Gr]=null,Gr--)}function ht(e,t){Gr++,id[Gr]=e.current,e.current=t}var Jo={},Jt=tr(Jo),hn=tr(!1),vr=Jo;function dl(e,t){var n=e.type.contextTypes;if(!n)return Jo;var o=e.stateNode;if(o&&o.__reactInternalMemoizedUnmaskedChildContext===t)return o.__reactInternalMemoizedMaskedChildContext;var r={},l;for(l in n)r[l]=t[l];return o&&(e=e.stateNode,e.__reactInternalMemoizedUnmaskedChildContext=t,e.__reactInternalMemoizedMaskedChildContext=r),r}function pn(e){return e=e.childContextTypes,e!=null}function Hs(){mt(hn),mt(Jt)}function m0(e,t,n){if(Jt.current!==Jo)throw Error(H(168));ht(Jt,t),ht(hn,n)}function Wf(e,t,n){var o=e.stateNode;if(t=t.childContextTypes,typeof o.getChildContext!="function")return n;o=o.getChildContext();for(var r in o)if(!(r in t))throw Error(H(108,o1(e)||"Unknown",r));return kt({},n,o)}function Us(e){return e=(e=e.stateNode)&&e.__reactInternalMemoizedMergedChildContext||Jo,vr=Jt.current,ht(Jt,e),ht(hn,hn.current),!0}function g0(e,t,n){var o=e.stateNode;if(!o)throw Error(H(169));n?(e=Wf(e,t,vr),o.__reactInternalMemoizedMergedChildContext=e,mt(hn),mt(Jt),ht(Jt,e)):mt(hn),ht(hn,n)}var bo=null,ca=!1,Sc=!1;function Ff(e){bo===null?bo=[e]:bo.push(e)}function yg(e){ca=!0,Ff(e)}function nr(){if(!Sc&&bo!==null){Sc=!0;var e=0,t=lt;try{var n=bo;for(lt=1;e<n.length;e++){var o=n[e];do o=o(!0);while(o!==null)}bo=null,ca=!1}catch(r){throw bo!==null&&(bo=bo.slice(e+1)),_f(Pd,nr),r}finally{lt=t,Sc=!1}}return null}var Zr=[],Jr=0,Ys=null,Xs=0,Rn=[],Pn=0,wr=null,ko=1,Co="";function fr(e,t){Zr[Jr++]=Xs,Zr[Jr++]=Ys,Ys=e,Xs=t}function jf(e,t,n){Rn[Pn++]=ko,Rn[Pn++]=Co,Rn[Pn++]=wr,wr=e;var o=ko;e=Co;var r=32-qn(o)-1;o&=~(1<<r),n+=1;var l=32-qn(t)+r;if(30<l){var i=r-r%5;l=(o&(1<<i)-1).toString(32),o>>=i,r-=i,ko=1<<32-qn(t)+r|n<<r|o,Co=l+e}else ko=1<<l|n<<r|o,Co=e}function jd(e){e.return!==null&&(fr(e,1),jf(e,1,0))}function Hd(e){for(;e===Ys;)Ys=Zr[--Jr],Zr[Jr]=null,Xs=Zr[--Jr],Zr[Jr]=null;for(;e===wr;)wr=Rn[--Pn],Rn[Pn]=null,Co=Rn[--Pn],Rn[Pn]=null,ko=Rn[--Pn],Rn[Pn]=null}var vn=null,xn=null,gt=!1,Kn=null;function Hf(e,t){var n=Tn(5,null,null,0);n.elementType="DELETED",n.stateNode=t,n.return=e,t=e.deletions,t===null?(e.deletions=[n],e.flags|=16):t.push(n)}function y0(e,t){switch(e.tag){case 5:var n=e.type;return t=t.nodeType!==1||n.toLowerCase()!==t.nodeName.toLowerCase()?null:t,t!==null?(e.stateNode=t,vn=e,xn=Qo(t.firstChild),!0):!1;case 6:return t=e.pendingProps===""||t.nodeType!==3?null:t,t!==null?(e.stateNode=t,vn=e,xn=null,!0):!1;case 13:return t=t.nodeType!==8?null:t,t!==null?(n=wr!==null?{id:ko,overflow:Co}:null,e.memoizedState={dehydrated:t,treeContext:n,retryLane:1073741824},n=Tn(18,null,null,0),n.stateNode=t,n.return=e,e.child=n,vn=e,xn=null,!0):!1;default:return!1}}function sd(e){return(e.mode&1)!==0&&(e.flags&128)===0}function ad(e){if(gt){var t=xn;if(t){var n=t;if(!y0(e,t)){if(sd(e))throw Error(H(418));t=Qo(n.nextSibling);var o=vn;t&&y0(e,t)?Hf(o,n):(e.flags=e.flags&-4097|2,gt=!1,vn=e)}}else{if(sd(e))throw Error(H(418));e.flags=e.flags&-4097|2,gt=!1,vn=e}}}function x0(e){for(e=e.return;e!==null&&e.tag!==5&&e.tag!==3&&e.tag!==13;)e=e.return;vn=e}function xs(e){if(e!==vn)return!1;if(!gt)return x0(e),gt=!0,!1;var t;if((t=e.tag!==3)&&!(t=e.tag!==5)&&(t=e.type,t=t!=="head"&&t!=="body"&&!od(e.type,e.memoizedProps)),t&&(t=xn)){if(sd(e))throw Uf(),Error(H(418));for(;t;)Hf(e,t),t=Qo(t.nextSibling)}if(x0(e),e.tag===13){if(e=e.memoizedState,e=e!==null?e.dehydrated:null,!e)throw Error(H(317));e:{for(e=e.nextSibling,t=0;e;){if(e.nodeType===8){var n=e.data;if(n==="/$"){if(t===0){xn=Qo(e.nextSibling);break e}t--}else n!=="$"&&n!=="$!"&&n!=="$?"||t++}e=e.nextSibling}xn=null}}else xn=vn?Qo(e.stateNode.nextSibling):null;return!0}function Uf(){for(var e=xn;e;)e=Qo(e.nextSibling)}function ul(){xn=vn=null,gt=!1}function Ud(e){Kn===null?Kn=[e]:Kn.push(e)}var xg=No.ReactCurrentBatchConfig;function Xl(e,t,n){if(e=n.ref,e!==null&&typeof e!="function"&&typeof e!="object"){if(n._owner){if(n=n._owner,n){if(n.tag!==1)throw Error(H(309));var o=n.stateNode}if(!o)throw Error(H(147,e));var r=o,l=""+e;return t!==null&&t.ref!==null&&typeof t.ref=="function"&&t.ref._stringRef===l?t.ref:(t=function(i){var s=r.refs;i===null?delete s[l]:s[l]=i},t._stringRef=l,t)}if(typeof e!="string")throw Error(H(284));if(!n._owner)throw Error(H(290,e))}return e}function vs(e,t){throw e=Object.prototype.toString.call(t),Error(H(31,e==="[object Object]"?"object with keys {"+Object.keys(t).join(", ")+"}":e))}function v0(e){var t=e._init;return t(e._payload)}function Yf(e){function t(f,g){if(e){var w=f.deletions;w===null?(f.deletions=[g],f.flags|=16):w.push(g)}}function n(f,g){if(!e)return null;for(;g!==null;)t(f,g),g=g.sibling;return null}function o(f,g){for(f=new Map;g!==null;)g.key!==null?f.set(g.key,g):f.set(g.index,g),g=g.sibling;return f}function r(f,g){return f=Go(f,g),f.index=0,f.sibling=null,f}function l(f,g,w){return f.index=w,e?(w=f.alternate,w!==null?(w=w.index,w<g?(f.flags|=2,g):w):(f.flags|=2,g)):(f.flags|=1048576,g)}function i(f){return e&&f.alternate===null&&(f.flags|=2),f}function s(f,g,w,$){return g===null||g.tag!==6?(g=Rc(w,f.mode,$),g.return=f,g):(g=r(g,w),g.return=f,g)}function a(f,g,w,$){var U=w.type;return U===Xr?p(f,g,w.props.children,$,w.key):g!==null&&(g.elementType===U||typeof U=="object"&&U!==null&&U.$$typeof===Oo&&v0(U)===g.type)?($=r(g,w.props),$.ref=Xl(f,g,w),$.return=f,$):($=Ps(w.type,w.key,w.props,null,f.mode,$),$.ref=Xl(f,g,w),$.return=f,$)}function m(f,g,w,$){return g===null||g.tag!==4||g.stateNode.containerInfo!==w.containerInfo||g.stateNode.implementation!==w.implementation?(g=Pc(w,f.mode,$),g.return=f,g):(g=r(g,w.children||[]),g.return=f,g)}function p(f,g,w,$,U){return g===null||g.tag!==7?(g=xr(w,f.mode,$,U),g.return=f,g):(g=r(g,w),g.return=f,g)}function b(f,g,w){if(typeof g=="string"&&g!==""||typeof g=="number")return g=Rc(""+g,f.mode,w),g.return=f,g;if(typeof g=="object"&&g!==null){switch(g.$$typeof){case ls:return w=Ps(g.type,g.key,g.props,null,f.mode,w),w.ref=Xl(f,null,g),w.return=f,w;case Yr:return g=Pc(g,f.mode,w),g.return=f,g;case Oo:var $=g._init;return b(f,$(g._payload),w)}if(Gl(g)||jl(g))return g=xr(g,f.mode,w,null),g.return=f,g;vs(f,g)}return null}function y(f,g,w,$){var U=g!==null?g.key:null;if(typeof w=="string"&&w!==""||typeof w=="number")return U!==null?null:s(f,g,""+w,$);if(typeof w=="object"&&w!==null){switch(w.$$typeof){case ls:return w.key===U?a(f,g,w,$):null;case Yr:return w.key===U?m(f,g,w,$):null;case Oo:return U=w._init,y(f,g,U(w._payload),$)}if(Gl(w)||jl(w))return U!==null?null:p(f,g,w,$,null);vs(f,w)}return null}function R(f,g,w,$,U){if(typeof $=="string"&&$!==""||typeof $=="number")return f=f.get(w)||null,s(g,f,""+$,U);if(typeof $=="object"&&$!==null){switch($.$$typeof){case ls:return f=f.get($.key===null?w:$.key)||null,a(g,f,$,U);case Yr:return f=f.get($.key===null?w:$.key)||null,m(g,f,$,U);case Oo:var V=$._init;return R(f,g,w,V($._payload),U)}if(Gl($)||jl($))return f=f.get(w)||null,p(g,f,$,U,null);vs(g,$)}return null}function C(f,g,w,$){for(var U=null,V=null,B=g,q=g=0,ye=null;B!==null&&q<w.length;q++){B.index>q?(ye=B,B=null):ye=B.sibling;var Z=y(f,B,w[q],$);if(Z===null){B===null&&(B=ye);break}e&&B&&Z.alternate===null&&t(f,B),g=l(Z,g,q),V===null?U=Z:V.sibling=Z,V=Z,B=ye}if(q===w.length)return n(f,B),gt&&fr(f,q),U;if(B===null){for(;q<w.length;q++)B=b(f,w[q],$),B!==null&&(g=l(B,g,q),V===null?U=B:V.sibling=B,V=B);return gt&&fr(f,q),U}for(B=o(f,B);q<w.length;q++)ye=R(B,f,q,w[q],$),ye!==null&&(e&&ye.alternate!==null&&B.delete(ye.key===null?q:ye.key),g=l(ye,g,q),V===null?U=ye:V.sibling=ye,V=ye);return e&&B.forEach(function(he){return t(f,he)}),gt&&fr(f,q),U}function N(f,g,w,$){var U=jl(w);if(typeof U!="function")throw Error(H(150));if(w=U.call(w),w==null)throw Error(H(151));for(var V=U=null,B=g,q=g=0,ye=null,Z=w.next();B!==null&&!Z.done;q++,Z=w.next()){B.index>q?(ye=B,B=null):ye=B.sibling;var he=y(f,B,Z.value,$);if(he===null){B===null&&(B=ye);break}e&&B&&he.alternate===null&&t(f,B),g=l(he,g,q),V===null?U=he:V.sibling=he,V=he,B=ye}if(Z.done)return n(f,B),gt&&fr(f,q),U;if(B===null){for(;!Z.done;q++,Z=w.next())Z=b(f,Z.value,$),Z!==null&&(g=l(Z,g,q),V===null?U=Z:V.sibling=Z,V=Z);return gt&&fr(f,q),U}for(B=o(f,B);!Z.done;q++,Z=w.next())Z=R(B,f,q,Z.value,$),Z!==null&&(e&&Z.alternate!==null&&B.delete(Z.key===null?q:Z.key),g=l(Z,g,q),V===null?U=Z:V.sibling=Z,V=Z);return e&&B.forEach(function(Ge){return t(f,Ge)}),gt&&fr(f,q),U}function L(f,g,w,$){if(typeof w=="object"&&w!==null&&w.type===Xr&&w.key===null&&(w=w.props.children),typeof w=="object"&&w!==null){switch(w.$$typeof){case ls:e:{for(var U=w.key,V=g;V!==null;){if(V.key===U){if(U=w.type,U===Xr){if(V.tag===7){n(f,V.sibling),g=r(V,w.props.children),g.return=f,f=g;break e}}else if(V.elementType===U||typeof U=="object"&&U!==null&&U.$$typeof===Oo&&v0(U)===V.type){n(f,V.sibling),g=r(V,w.props),g.ref=Xl(f,V,w),g.return=f,f=g;break e}n(f,V);break}else t(f,V);V=V.sibling}w.type===Xr?(g=xr(w.props.children,f.mode,$,w.key),g.return=f,f=g):($=Ps(w.type,w.key,w.props,null,f.mode,$),$.ref=Xl(f,g,w),$.return=f,f=$)}return i(f);case Yr:e:{for(V=w.key;g!==null;){if(g.key===V)if(g.tag===4&&g.stateNode.containerInfo===w.containerInfo&&g.stateNode.implementation===w.implementation){n(f,g.sibling),g=r(g,w.children||[]),g.return=f,f=g;break e}else{n(f,g);break}else t(f,g);g=g.sibling}g=Pc(w,f.mode,$),g.return=f,f=g}return i(f);case Oo:return V=w._init,L(f,g,V(w._payload),$)}if(Gl(w))return C(f,g,w,$);if(jl(w))return N(f,g,w,$);vs(f,w)}return typeof w=="string"&&w!==""||typeof w=="number"?(w=""+w,g!==null&&g.tag===6?(n(f,g.sibling),g=r(g,w),g.return=f,f=g):(n(f,g),g=Rc(w,f.mode,$),g.return=f,f=g),i(f)):n(f,g)}return L}var _l=Yf(!0),Xf=Yf(!1),Qs=tr(null),Vs=null,el=null,Yd=null;function Xd(){Yd=el=Vs=null}function Qd(e){var t=Qs.current;mt(Qs),e._currentValue=t}function cd(e,t,n){for(;e!==null;){var o=e.alternate;if((e.childLanes&t)!==t?(e.childLanes|=t,o!==null&&(o.childLanes|=t)):o!==null&&(o.childLanes&t)!==t&&(o.childLanes|=t),e===n)break;e=e.return}}function sl(e,t){Vs=e,Yd=el=null,e=e.dependencies,e!==null&&e.firstContext!==null&&((e.lanes&t)!==0&&(fn=!0),e.firstContext=null)}function Bn(e){var t=e._currentValue;if(Yd!==e)if(e={context:e,memoizedValue:t,next:null},el===null){if(Vs===null)throw Error(H(308));el=e,Vs.dependencies={lanes:0,firstContext:e}}else el=el.next=e;return t}var mr=null;function Vd(e){mr===null?mr=[e]:mr.push(e)}function Qf(e,t,n,o){var r=t.interleaved;return r===null?(n.next=n,Vd(t)):(n.next=r.next,r.next=n),t.interleaved=n,Lo(e,o)}function Lo(e,t){e.lanes|=t;var n=e.alternate;for(n!==null&&(n.lanes|=t),n=e,e=e.return;e!==null;)e.childLanes|=t,n=e.alternate,n!==null&&(n.childLanes|=t),n=e,e=e.return;return n.tag===3?n.stateNode:null}var Ao=!1;function Kd(e){e.updateQueue={baseState:e.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,interleaved:null,lanes:0},effects:null}}function Vf(e,t){e=e.updateQueue,t.updateQueue===e&&(t.updateQueue={baseState:e.baseState,firstBaseUpdate:e.firstBaseUpdate,lastBaseUpdate:e.lastBaseUpdate,shared:e.shared,effects:e.effects})}function So(e,t){return{eventTime:e,lane:t,tag:0,payload:null,callback:null,next:null}}function Vo(e,t,n){var o=e.updateQueue;if(o===null)return null;if(o=o.shared,(Ve&2)!==0){var r=o.pending;return r===null?t.next=t:(t.next=r.next,r.next=t),o.pending=t,Lo(e,n)}return r=o.interleaved,r===null?(t.next=t,Vd(o)):(t.next=r.next,r.next=t),o.interleaved=t,Lo(e,n)}function Es(e,t,n){if(t=t.updateQueue,t!==null&&(t=t.shared,(n&4194240)!==0)){var o=t.lanes;o&=e.pendingLanes,n|=o,t.lanes=n,Td(e,n)}}function w0(e,t){var n=e.updateQueue,o=e.alternate;if(o!==null&&(o=o.updateQueue,n===o)){var r=null,l=null;if(n=n.firstBaseUpdate,n!==null){do{var i={eventTime:n.eventTime,lane:n.lane,tag:n.tag,payload:n.payload,callback:n.callback,next:null};l===null?r=l=i:l=l.next=i,n=n.next}while(n!==null);l===null?r=l=t:l=l.next=t}else r=l=t;n={baseState:o.baseState,firstBaseUpdate:r,lastBaseUpdate:l,shared:o.shared,effects:o.effects},e.updateQueue=n;return}e=n.lastBaseUpdate,e===null?n.firstBaseUpdate=t:e.next=t,n.lastBaseUpdate=t}function Ks(e,t,n,o){var r=e.updateQueue;Ao=!1;var l=r.firstBaseUpdate,i=r.lastBaseUpdate,s=r.shared.pending;if(s!==null){r.shared.pending=null;var a=s,m=a.next;a.next=null,i===null?l=m:i.next=m,i=a;var p=e.alternate;p!==null&&(p=p.updateQueue,s=p.lastBaseUpdate,s!==i&&(s===null?p.firstBaseUpdate=m:s.next=m,p.lastBaseUpdate=a))}if(l!==null){var b=r.baseState;i=0,p=m=a=null,s=l;do{var y=s.lane,R=s.eventTime;if((o&y)===y){p!==null&&(p=p.next={eventTime:R,lane:0,tag:s.tag,payload:s.payload,callback:s.callback,next:null});e:{var C=e,N=s;switch(y=t,R=n,N.tag){case 1:if(C=N.payload,typeof C=="function"){b=C.call(R,b,y);break e}b=C;break e;case 3:C.flags=C.flags&-65537|128;case 0:if(C=N.payload,y=typeof C=="function"?C.call(R,b,y):C,y==null)break e;b=kt({},b,y);break e;case 2:Ao=!0}}s.callback!==null&&s.lane!==0&&(e.flags|=64,y=r.effects,y===null?r.effects=[s]:y.push(s))}else R={eventTime:R,lane:y,tag:s.tag,payload:s.payload,callback:s.callback,next:null},p===null?(m=p=R,a=b):p=p.next=R,i|=y;if(s=s.next,s===null){if(s=r.shared.pending,s===null)break;y=s,s=y.next,y.next=null,r.lastBaseUpdate=y,r.shared.pending=null}}while(!0);if(p===null&&(a=b),r.baseState=a,r.firstBaseUpdate=m,r.lastBaseUpdate=p,t=r.shared.interleaved,t!==null){r=t;do i|=r.lane,r=r.next;while(r!==t)}else l===null&&(r.shared.lanes=0);kr|=i,e.lanes=i,e.memoizedState=b}}function b0(e,t,n){if(e=t.effects,t.effects=null,e!==null)for(t=0;t<e.length;t++){var o=e[t],r=o.callback;if(r!==null){if(o.callback=null,o=n,typeof r!="function")throw Error(H(191,r));r.call(o)}}}var Ii={},fo=tr(Ii),vi=tr(Ii),wi=tr(Ii);function gr(e){if(e===Ii)throw Error(H(174));return e}function qd(e,t){switch(ht(wi,t),ht(vi,e),ht(fo,Ii),e=t.nodeType,e){case 9:case 11:t=(t=t.documentElement)?t.namespaceURI:Hc(null,"");break;default:e=e===8?t.parentNode:t,t=e.namespaceURI||null,e=e.tagName,t=Hc(t,e)}mt(fo),ht(fo,t)}function fl(){mt(fo),mt(vi),mt(wi)}function Kf(e){gr(wi.current);var t=gr(fo.current),n=Hc(t,e.type);t!==n&&(ht(vi,e),ht(fo,n))}function Gd(e){vi.current===e&&(mt(fo),mt(vi))}var wt=tr(0);function qs(e){for(var t=e;t!==null;){if(t.tag===13){var n=t.memoizedState;if(n!==null&&(n=n.dehydrated,n===null||n.data==="$?"||n.data==="$!"))return t}else if(t.tag===19&&t.memoizedProps.revealOrder!==void 0){if((t.flags&128)!==0)return t}else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===e)break;for(;t.sibling===null;){if(t.return===null||t.return===e)return null;t=t.return}t.sibling.return=t.return,t=t.sibling}return null}var Mc=[];function Zd(){for(var e=0;e<Mc.length;e++)Mc[e]._workInProgressVersionPrimary=null;Mc.length=0}var Ls=No.ReactCurrentDispatcher,Ec=No.ReactCurrentBatchConfig,br=0,bt=null,At=null,jt=null,Gs=!1,li=!1,bi=0,vg=0;function qt(){throw Error(H(321))}function Jd(e,t){if(t===null)return!1;for(var n=0;n<t.length&&n<e.length;n++)if(!Zn(e[n],t[n]))return!1;return!0}function eu(e,t,n,o,r,l){if(br=l,bt=t,t.memoizedState=null,t.updateQueue=null,t.lanes=0,Ls.current=e===null||e.memoizedState===null?Cg:Sg,e=n(o,r),li){l=0;do{if(li=!1,bi=0,25<=l)throw Error(H(301));l+=1,jt=At=null,t.updateQueue=null,Ls.current=Mg,e=n(o,r)}while(li)}if(Ls.current=Zs,t=At!==null&&At.next!==null,br=0,jt=At=bt=null,Gs=!1,t)throw Error(H(300));return e}function tu(){var e=bi!==0;return bi=0,e}function co(){var e={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return jt===null?bt.memoizedState=jt=e:jt=jt.next=e,jt}function zn(){if(At===null){var e=bt.alternate;e=e!==null?e.memoizedState:null}else e=At.next;var t=jt===null?bt.memoizedState:jt.next;if(t!==null)jt=t,At=e;else{if(e===null)throw Error(H(310));At=e,e={memoizedState:At.memoizedState,baseState:At.baseState,baseQueue:At.baseQueue,queue:At.queue,next:null},jt===null?bt.memoizedState=jt=e:jt=jt.next=e}return jt}function ki(e,t){return typeof t=="function"?t(e):t}function Lc(e){var t=zn(),n=t.queue;if(n===null)throw Error(H(311));n.lastRenderedReducer=e;var o=At,r=o.baseQueue,l=n.pending;if(l!==null){if(r!==null){var i=r.next;r.next=l.next,l.next=i}o.baseQueue=r=l,n.pending=null}if(r!==null){l=r.next,o=o.baseState;var s=i=null,a=null,m=l;do{var p=m.lane;if((br&p)===p)a!==null&&(a=a.next={lane:0,action:m.action,hasEagerState:m.hasEagerState,eagerState:m.eagerState,next:null}),o=m.hasEagerState?m.eagerState:e(o,m.action);else{var b={lane:p,action:m.action,hasEagerState:m.hasEagerState,eagerState:m.eagerState,next:null};a===null?(s=a=b,i=o):a=a.next=b,bt.lanes|=p,kr|=p}m=m.next}while(m!==null&&m!==l);a===null?i=o:a.next=s,Zn(o,t.memoizedState)||(fn=!0),t.memoizedState=o,t.baseState=i,t.baseQueue=a,n.lastRenderedState=o}if(e=n.interleaved,e!==null){r=e;do l=r.lane,bt.lanes|=l,kr|=l,r=r.next;while(r!==e)}else r===null&&(n.lanes=0);return[t.memoizedState,n.dispatch]}function Ic(e){var t=zn(),n=t.queue;if(n===null)throw Error(H(311));n.lastRenderedReducer=e;var o=n.dispatch,r=n.pending,l=t.memoizedState;if(r!==null){n.pending=null;var i=r=r.next;do l=e(l,i.action),i=i.next;while(i!==r);Zn(l,t.memoizedState)||(fn=!0),t.memoizedState=l,t.baseQueue===null&&(t.baseState=l),n.lastRenderedState=l}return[l,o]}function qf(){}function Gf(e,t){var n=bt,o=zn(),r=t(),l=!Zn(o.memoizedState,r);if(l&&(o.memoizedState=r,fn=!0),o=o.queue,nu(eh.bind(null,n,o,e),[e]),o.getSnapshot!==t||l||jt!==null&&jt.memoizedState.tag&1){if(n.flags|=2048,Ci(9,Jf.bind(null,n,o,r,t),void 0,null),Ht===null)throw Error(H(349));(br&30)!==0||Zf(n,t,r)}return r}function Zf(e,t,n){e.flags|=16384,e={getSnapshot:t,value:n},t=bt.updateQueue,t===null?(t={lastEffect:null,stores:null},bt.updateQueue=t,t.stores=[e]):(n=t.stores,n===null?t.stores=[e]:n.push(e))}function Jf(e,t,n,o){t.value=n,t.getSnapshot=o,th(t)&&nh(e)}function eh(e,t,n){return n(function(){th(t)&&nh(e)})}function th(e){var t=e.getSnapshot;e=e.value;try{var n=t();return!Zn(e,n)}catch{return!0}}function nh(e){var t=Lo(e,1);t!==null&&Gn(t,e,1,-1)}function k0(e){var t=co();return typeof e=="function"&&(e=e()),t.memoizedState=t.baseState=e,e={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:ki,lastRenderedState:e},t.queue=e,e=e.dispatch=kg.bind(null,bt,e),[t.memoizedState,e]}function Ci(e,t,n,o){return e={tag:e,create:t,destroy:n,deps:o,next:null},t=bt.updateQueue,t===null?(t={lastEffect:null,stores:null},bt.updateQueue=t,t.lastEffect=e.next=e):(n=t.lastEffect,n===null?t.lastEffect=e.next=e:(o=n.next,n.next=e,e.next=o,t.lastEffect=e)),e}function oh(){return zn().memoizedState}function Is(e,t,n,o){var r=co();bt.flags|=e,r.memoizedState=Ci(1|t,n,void 0,o===void 0?null:o)}function da(e,t,n,o){var r=zn();o=o===void 0?null:o;var l=void 0;if(At!==null){var i=At.memoizedState;if(l=i.destroy,o!==null&&Jd(o,i.deps)){r.memoizedState=Ci(t,n,l,o);return}}bt.flags|=e,r.memoizedState=Ci(1|t,n,l,o)}function C0(e,t){return Is(8390656,8,e,t)}function nu(e,t){return da(2048,8,e,t)}function rh(e,t){return da(4,2,e,t)}function lh(e,t){return da(4,4,e,t)}function ih(e,t){if(typeof t=="function")return e=e(),t(e),function(){t(null)};if(t!=null)return e=e(),t.current=e,function(){t.current=null}}function sh(e,t,n){return n=n!=null?n.concat([e]):null,da(4,4,ih.bind(null,t,e),n)}function ou(){}function ah(e,t){var n=zn();t=t===void 0?null:t;var o=n.memoizedState;return o!==null&&t!==null&&Jd(t,o[1])?o[0]:(n.memoizedState=[e,t],e)}function ch(e,t){var n=zn();t=t===void 0?null:t;var o=n.memoizedState;return o!==null&&t!==null&&Jd(t,o[1])?o[0]:(e=e(),n.memoizedState=[e,t],e)}function dh(e,t,n){return(br&21)===0?(e.baseState&&(e.baseState=!1,fn=!0),e.memoizedState=n):(Zn(n,t)||(n=pf(),bt.lanes|=n,kr|=n,e.baseState=!0),t)}function wg(e,t){var n=lt;lt=n!==0&&4>n?n:4,e(!0);var o=Ec.transition;Ec.transition={};try{e(!1),t()}finally{lt=n,Ec.transition=o}}function uh(){return zn().memoizedState}function bg(e,t,n){var o=qo(e);if(n={lane:o,action:n,hasEagerState:!1,eagerState:null,next:null},_h(e))fh(t,n);else if(n=Qf(e,t,n,o),n!==null){var r=rn();Gn(n,e,o,r),hh(n,t,o)}}function kg(e,t,n){var o=qo(e),r={lane:o,action:n,hasEagerState:!1,eagerState:null,next:null};if(_h(e))fh(t,r);else{var l=e.alternate;if(e.lanes===0&&(l===null||l.lanes===0)&&(l=t.lastRenderedReducer,l!==null))try{var i=t.lastRenderedState,s=l(i,n);if(r.hasEagerState=!0,r.eagerState=s,Zn(s,i)){var a=t.interleaved;a===null?(r.next=r,Vd(t)):(r.next=a.next,a.next=r),t.interleaved=r;return}}catch{}finally{}n=Qf(e,t,r,o),n!==null&&(r=rn(),Gn(n,e,o,r),hh(n,t,o))}}function _h(e){var t=e.alternate;return e===bt||t!==null&&t===bt}function fh(e,t){li=Gs=!0;var n=e.pending;n===null?t.next=t:(t.next=n.next,n.next=t),e.pending=t}function hh(e,t,n){if((n&4194240)!==0){var o=t.lanes;o&=e.pendingLanes,n|=o,t.lanes=n,Td(e,n)}}var Zs={readContext:Bn,useCallback:qt,useContext:qt,useEffect:qt,useImperativeHandle:qt,useInsertionEffect:qt,useLayoutEffect:qt,useMemo:qt,useReducer:qt,useRef:qt,useState:qt,useDebugValue:qt,useDeferredValue:qt,useTransition:qt,useMutableSource:qt,useSyncExternalStore:qt,useId:qt,unstable_isNewReconciler:!1},Cg={readContext:Bn,useCallback:function(e,t){return co().memoizedState=[e,t===void 0?null:t],e},useContext:Bn,useEffect:C0,useImperativeHandle:function(e,t,n){return n=n!=null?n.concat([e]):null,Is(4194308,4,ih.bind(null,t,e),n)},useLayoutEffect:function(e,t){return Is(4194308,4,e,t)},useInsertionEffect:function(e,t){return Is(4,2,e,t)},useMemo:function(e,t){var n=co();return t=t===void 0?null:t,e=e(),n.memoizedState=[e,t],e},useReducer:function(e,t,n){var o=co();return t=n!==void 0?n(t):t,o.memoizedState=o.baseState=t,e={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:e,lastRenderedState:t},o.queue=e,e=e.dispatch=bg.bind(null,bt,e),[o.memoizedState,e]},useRef:function(e){var t=co();return e={current:e},t.memoizedState=e},useState:k0,useDebugValue:ou,useDeferredValue:function(e){return co().memoizedState=e},useTransition:function(){var e=k0(!1),t=e[0];return e=wg.bind(null,e[1]),co().memoizedState=e,[t,e]},useMutableSource:function(){},useSyncExternalStore:function(e,t,n){var o=bt,r=co();if(gt){if(n===void 0)throw Error(H(407));n=n()}else{if(n=t(),Ht===null)throw Error(H(349));(br&30)!==0||Zf(o,t,n)}r.memoizedState=n;var l={value:n,getSnapshot:t};return r.queue=l,C0(eh.bind(null,o,l,e),[e]),o.flags|=2048,Ci(9,Jf.bind(null,o,l,n,t),void 0,null),n},useId:function(){var e=co(),t=Ht.identifierPrefix;if(gt){var n=Co,o=ko;n=(o&~(1<<32-qn(o)-1)).toString(32)+n,t=":"+t+"R"+n,n=bi++,0<n&&(t+="H"+n.toString(32)),t+=":"}else n=vg++,t=":"+t+"r"+n.toString(32)+":";return e.memoizedState=t},unstable_isNewReconciler:!1},Sg={readContext:Bn,useCallback:ah,useContext:Bn,useEffect:nu,useImperativeHandle:sh,useInsertionEffect:rh,useLayoutEffect:lh,useMemo:ch,useReducer:Lc,useRef:oh,useState:function(){return Lc(ki)},useDebugValue:ou,useDeferredValue:function(e){var t=zn();return dh(t,At.memoizedState,e)},useTransition:function(){var e=Lc(ki)[0],t=zn().memoizedState;return[e,t]},useMutableSource:qf,useSyncExternalStore:Gf,useId:uh,unstable_isNewReconciler:!1},Mg={readContext:Bn,useCallback:ah,useContext:Bn,useEffect:nu,useImperativeHandle:sh,useInsertionEffect:rh,useLayoutEffect:lh,useMemo:ch,useReducer:Ic,useRef:oh,useState:function(){return Ic(ki)},useDebugValue:ou,useDeferredValue:function(e){var t=zn();return At===null?t.memoizedState=e:dh(t,At.memoizedState,e)},useTransition:function(){var e=Ic(ki)[0],t=zn().memoizedState;return[e,t]},useMutableSource:qf,useSyncExternalStore:Gf,useId:uh,unstable_isNewReconciler:!1};function Qn(e,t){if(e&&e.defaultProps){t=kt({},t),e=e.defaultProps;for(var n in e)t[n]===void 0&&(t[n]=e[n]);return t}return t}function dd(e,t,n,o){t=e.memoizedState,n=n(o,t),n=n==null?t:kt({},t,n),e.memoizedState=n,e.lanes===0&&(e.updateQueue.baseState=n)}var ua={isMounted:function(e){return(e=e._reactInternals)?Mr(e)===e:!1},enqueueSetState:function(e,t,n){e=e._reactInternals;var o=rn(),r=qo(e),l=So(o,r);l.payload=t,n!=null&&(l.callback=n),t=Vo(e,l,r),t!==null&&(Gn(t,e,r,o),Es(t,e,r))},enqueueReplaceState:function(e,t,n){e=e._reactInternals;var o=rn(),r=qo(e),l=So(o,r);l.tag=1,l.payload=t,n!=null&&(l.callback=n),t=Vo(e,l,r),t!==null&&(Gn(t,e,r,o),Es(t,e,r))},enqueueForceUpdate:function(e,t){e=e._reactInternals;var n=rn(),o=qo(e),r=So(n,o);r.tag=2,t!=null&&(r.callback=t),t=Vo(e,r,o),t!==null&&(Gn(t,e,o,n),Es(t,e,o))}};function S0(e,t,n,o,r,l,i){return e=e.stateNode,typeof e.shouldComponentUpdate=="function"?e.shouldComponentUpdate(o,l,i):t.prototype&&t.prototype.isPureReactComponent?!mi(n,o)||!mi(r,l):!0}function ph(e,t,n){var o=!1,r=Jo,l=t.contextType;return typeof l=="object"&&l!==null?l=Bn(l):(r=pn(t)?vr:Jt.current,o=t.contextTypes,l=(o=o!=null)?dl(e,r):Jo),t=new t(n,l),e.memoizedState=t.state!==null&&t.state!==void 0?t.state:null,t.updater=ua,e.stateNode=t,t._reactInternals=e,o&&(e=e.stateNode,e.__reactInternalMemoizedUnmaskedChildContext=r,e.__reactInternalMemoizedMaskedChildContext=l),t}function M0(e,t,n,o){e=t.state,typeof t.componentWillReceiveProps=="function"&&t.componentWillReceiveProps(n,o),typeof t.UNSAFE_componentWillReceiveProps=="function"&&t.UNSAFE_componentWillReceiveProps(n,o),t.state!==e&&ua.enqueueReplaceState(t,t.state,null)}function ud(e,t,n,o){var r=e.stateNode;r.props=n,r.state=e.memoizedState,r.refs={},Kd(e);var l=t.contextType;typeof l=="object"&&l!==null?r.context=Bn(l):(l=pn(t)?vr:Jt.current,r.context=dl(e,l)),r.state=e.memoizedState,l=t.getDerivedStateFromProps,typeof l=="function"&&(dd(e,t,l,n),r.state=e.memoizedState),typeof t.getDerivedStateFromProps=="function"||typeof r.getSnapshotBeforeUpdate=="function"||typeof r.UNSAFE_componentWillMount!="function"&&typeof r.componentWillMount!="function"||(t=r.state,typeof r.componentWillMount=="function"&&r.componentWillMount(),typeof r.UNSAFE_componentWillMount=="function"&&r.UNSAFE_componentWillMount(),t!==r.state&&ua.enqueueReplaceState(r,r.state,null),Ks(e,n,r,o),r.state=e.memoizedState),typeof r.componentDidMount=="function"&&(e.flags|=4194308)}function hl(e,t){try{var n="",o=t;do n+=n1(o),o=o.return;while(o);var r=n}catch(l){r=`
Error generating stack: `+l.message+`
`+l.stack}return{value:e,source:t,stack:r,digest:null}}function Nc(e,t,n){return{value:e,source:null,stack:n??null,digest:t??null}}function _d(e,t){try{console.error(t.value)}catch(n){setTimeout(function(){throw n})}}var Eg=typeof WeakMap=="function"?WeakMap:Map;function mh(e,t,n){n=So(-1,n),n.tag=3,n.payload={element:null};var o=t.value;return n.callback=function(){ea||(ea=!0,bd=o),_d(e,t)},n}function gh(e,t,n){n=So(-1,n),n.tag=3;var o=e.type.getDerivedStateFromError;if(typeof o=="function"){var r=t.value;n.payload=function(){return o(r)},n.callback=function(){_d(e,t)}}var l=e.stateNode;return l!==null&&typeof l.componentDidCatch=="function"&&(n.callback=function(){_d(e,t),typeof o!="function"&&(Ko===null?Ko=new Set([this]):Ko.add(this));var i=t.stack;this.componentDidCatch(t.value,{componentStack:i!==null?i:""})}),n}function E0(e,t,n){var o=e.pingCache;if(o===null){o=e.pingCache=new Eg;var r=new Set;o.set(t,r)}else r=o.get(t),r===void 0&&(r=new Set,o.set(t,r));r.has(n)||(r.add(n),e=Fg.bind(null,e,t,n),t.then(e,e))}function L0(e){do{var t;if((t=e.tag===13)&&(t=e.memoizedState,t=t!==null?t.dehydrated!==null:!0),t)return e;e=e.return}while(e!==null);return null}function I0(e,t,n,o,r){return(e.mode&1)===0?(e===t?e.flags|=65536:(e.flags|=128,n.flags|=131072,n.flags&=-52805,n.tag===1&&(n.alternate===null?n.tag=17:(t=So(-1,1),t.tag=2,Vo(n,t,1))),n.lanes|=1),e):(e.flags|=65536,e.lanes=r,e)}var Lg=No.ReactCurrentOwner,fn=!1;function on(e,t,n,o){t.child=e===null?Xf(t,null,n,o):_l(t,e.child,n,o)}function N0(e,t,n,o,r){n=n.render;var l=t.ref;return sl(t,r),o=eu(e,t,n,o,l,r),n=tu(),e!==null&&!fn?(t.updateQueue=e.updateQueue,t.flags&=-2053,e.lanes&=~r,Io(e,t,r)):(gt&&n&&jd(t),t.flags|=1,on(e,t,o,r),t.child)}function $0(e,t,n,o,r){if(e===null){var l=n.type;return typeof l=="function"&&!uu(l)&&l.defaultProps===void 0&&n.compare===null&&n.defaultProps===void 0?(t.tag=15,t.type=l,yh(e,t,l,o,r)):(e=Ps(n.type,null,o,t,t.mode,r),e.ref=t.ref,e.return=t,t.child=e)}if(l=e.child,(e.lanes&r)===0){var i=l.memoizedProps;if(n=n.compare,n=n!==null?n:mi,n(i,o)&&e.ref===t.ref)return Io(e,t,r)}return t.flags|=1,e=Go(l,o),e.ref=t.ref,e.return=t,t.child=e}function yh(e,t,n,o,r){if(e!==null){var l=e.memoizedProps;if(mi(l,o)&&e.ref===t.ref)if(fn=!1,t.pendingProps=o=l,(e.lanes&r)!==0)(e.flags&131072)!==0&&(fn=!0);else return t.lanes=e.lanes,Io(e,t,r)}return fd(e,t,n,o,r)}function xh(e,t,n){var o=t.pendingProps,r=o.children,l=e!==null?e.memoizedState:null;if(o.mode==="hidden")if((t.mode&1)===0)t.memoizedState={baseLanes:0,cachePool:null,transitions:null},ht(nl,yn),yn|=n;else{if((n&1073741824)===0)return e=l!==null?l.baseLanes|n:n,t.lanes=t.childLanes=1073741824,t.memoizedState={baseLanes:e,cachePool:null,transitions:null},t.updateQueue=null,ht(nl,yn),yn|=e,null;t.memoizedState={baseLanes:0,cachePool:null,transitions:null},o=l!==null?l.baseLanes:n,ht(nl,yn),yn|=o}else l!==null?(o=l.baseLanes|n,t.memoizedState=null):o=n,ht(nl,yn),yn|=o;return on(e,t,r,n),t.child}function vh(e,t){var n=t.ref;(e===null&&n!==null||e!==null&&e.ref!==n)&&(t.flags|=512,t.flags|=2097152)}function fd(e,t,n,o,r){var l=pn(n)?vr:Jt.current;return l=dl(t,l),sl(t,r),n=eu(e,t,n,o,l,r),o=tu(),e!==null&&!fn?(t.updateQueue=e.updateQueue,t.flags&=-2053,e.lanes&=~r,Io(e,t,r)):(gt&&o&&jd(t),t.flags|=1,on(e,t,n,r),t.child)}function R0(e,t,n,o,r){if(pn(n)){var l=!0;Us(t)}else l=!1;if(sl(t,r),t.stateNode===null)Ns(e,t),ph(t,n,o),ud(t,n,o,r),o=!0;else if(e===null){var i=t.stateNode,s=t.memoizedProps;i.props=s;var a=i.context,m=n.contextType;typeof m=="object"&&m!==null?m=Bn(m):(m=pn(n)?vr:Jt.current,m=dl(t,m));var p=n.getDerivedStateFromProps,b=typeof p=="function"||typeof i.getSnapshotBeforeUpdate=="function";b||typeof i.UNSAFE_componentWillReceiveProps!="function"&&typeof i.componentWillReceiveProps!="function"||(s!==o||a!==m)&&M0(t,i,o,m),Ao=!1;var y=t.memoizedState;i.state=y,Ks(t,o,i,r),a=t.memoizedState,s!==o||y!==a||hn.current||Ao?(typeof p=="function"&&(dd(t,n,p,o),a=t.memoizedState),(s=Ao||S0(t,n,s,o,y,a,m))?(b||typeof i.UNSAFE_componentWillMount!="function"&&typeof i.componentWillMount!="function"||(typeof i.componentWillMount=="function"&&i.componentWillMount(),typeof i.UNSAFE_componentWillMount=="function"&&i.UNSAFE_componentWillMount()),typeof i.componentDidMount=="function"&&(t.flags|=4194308)):(typeof i.componentDidMount=="function"&&(t.flags|=4194308),t.memoizedProps=o,t.memoizedState=a),i.props=o,i.state=a,i.context=m,o=s):(typeof i.componentDidMount=="function"&&(t.flags|=4194308),o=!1)}else{i=t.stateNode,Vf(e,t),s=t.memoizedProps,m=t.type===t.elementType?s:Qn(t.type,s),i.props=m,b=t.pendingProps,y=i.context,a=n.contextType,typeof a=="object"&&a!==null?a=Bn(a):(a=pn(n)?vr:Jt.current,a=dl(t,a));var R=n.getDerivedStateFromProps;(p=typeof R=="function"||typeof i.getSnapshotBeforeUpdate=="function")||typeof i.UNSAFE_componentWillReceiveProps!="function"&&typeof i.componentWillReceiveProps!="function"||(s!==b||y!==a)&&M0(t,i,o,a),Ao=!1,y=t.memoizedState,i.state=y,Ks(t,o,i,r);var C=t.memoizedState;s!==b||y!==C||hn.current||Ao?(typeof R=="function"&&(dd(t,n,R,o),C=t.memoizedState),(m=Ao||S0(t,n,m,o,y,C,a)||!1)?(p||typeof i.UNSAFE_componentWillUpdate!="function"&&typeof i.componentWillUpdate!="function"||(typeof i.componentWillUpdate=="function"&&i.componentWillUpdate(o,C,a),typeof i.UNSAFE_componentWillUpdate=="function"&&i.UNSAFE_componentWillUpdate(o,C,a)),typeof i.componentDidUpdate=="function"&&(t.flags|=4),typeof i.getSnapshotBeforeUpdate=="function"&&(t.flags|=1024)):(typeof i.componentDidUpdate!="function"||s===e.memoizedProps&&y===e.memoizedState||(t.flags|=4),typeof i.getSnapshotBeforeUpdate!="function"||s===e.memoizedProps&&y===e.memoizedState||(t.flags|=1024),t.memoizedProps=o,t.memoizedState=C),i.props=o,i.state=C,i.context=a,o=m):(typeof i.componentDidUpdate!="function"||s===e.memoizedProps&&y===e.memoizedState||(t.flags|=4),typeof i.getSnapshotBeforeUpdate!="function"||s===e.memoizedProps&&y===e.memoizedState||(t.flags|=1024),o=!1)}return hd(e,t,n,o,l,r)}function hd(e,t,n,o,r,l){vh(e,t);var i=(t.flags&128)!==0;if(!o&&!i)return r&&g0(t,n,!1),Io(e,t,l);o=t.stateNode,Lg.current=t;var s=i&&typeof n.getDerivedStateFromError!="function"?null:o.render();return t.flags|=1,e!==null&&i?(t.child=_l(t,e.child,null,l),t.child=_l(t,null,s,l)):on(e,t,s,l),t.memoizedState=o.state,r&&g0(t,n,!0),t.child}function wh(e){var t=e.stateNode;t.pendingContext?m0(e,t.pendingContext,t.pendingContext!==t.context):t.context&&m0(e,t.context,!1),qd(e,t.containerInfo)}function P0(e,t,n,o,r){return ul(),Ud(r),t.flags|=256,on(e,t,n,o),t.child}var pd={dehydrated:null,treeContext:null,retryLane:0};function md(e){return{baseLanes:e,cachePool:null,transitions:null}}function bh(e,t,n){var o=t.pendingProps,r=wt.current,l=!1,i=(t.flags&128)!==0,s;if((s=i)||(s=e!==null&&e.memoizedState===null?!1:(r&2)!==0),s?(l=!0,t.flags&=-129):(e===null||e.memoizedState!==null)&&(r|=1),ht(wt,r&1),e===null)return ad(t),e=t.memoizedState,e!==null&&(e=e.dehydrated,e!==null)?((t.mode&1)===0?t.lanes=1:e.data==="$!"?t.lanes=8:t.lanes=1073741824,null):(i=o.children,e=o.fallback,l?(o=t.mode,l=t.child,i={mode:"hidden",children:i},(o&1)===0&&l!==null?(l.childLanes=0,l.pendingProps=i):l=ha(i,o,0,null),e=xr(e,o,n,null),l.return=t,e.return=t,l.sibling=e,t.child=l,t.child.memoizedState=md(n),t.memoizedState=pd,e):ru(t,i));if(r=e.memoizedState,r!==null&&(s=r.dehydrated,s!==null))return Ig(e,t,i,o,s,r,n);if(l){l=o.fallback,i=t.mode,r=e.child,s=r.sibling;var a={mode:"hidden",children:o.children};return(i&1)===0&&t.child!==r?(o=t.child,o.childLanes=0,o.pendingProps=a,t.deletions=null):(o=Go(r,a),o.subtreeFlags=r.subtreeFlags&14680064),s!==null?l=Go(s,l):(l=xr(l,i,n,null),l.flags|=2),l.return=t,o.return=t,o.sibling=l,t.child=o,o=l,l=t.child,i=e.child.memoizedState,i=i===null?md(n):{baseLanes:i.baseLanes|n,cachePool:null,transitions:i.transitions},l.memoizedState=i,l.childLanes=e.childLanes&~n,t.memoizedState=pd,o}return l=e.child,e=l.sibling,o=Go(l,{mode:"visible",children:o.children}),(t.mode&1)===0&&(o.lanes=n),o.return=t,o.sibling=null,e!==null&&(n=t.deletions,n===null?(t.deletions=[e],t.flags|=16):n.push(e)),t.child=o,t.memoizedState=null,o}function ru(e,t){return t=ha({mode:"visible",children:t},e.mode,0,null),t.return=e,e.child=t}function ws(e,t,n,o){return o!==null&&Ud(o),_l(t,e.child,null,n),e=ru(t,t.pendingProps.children),e.flags|=2,t.memoizedState=null,e}function Ig(e,t,n,o,r,l,i){if(n)return t.flags&256?(t.flags&=-257,o=Nc(Error(H(422))),ws(e,t,i,o)):t.memoizedState!==null?(t.child=e.child,t.flags|=128,null):(l=o.fallback,r=t.mode,o=ha({mode:"visible",children:o.children},r,0,null),l=xr(l,r,i,null),l.flags|=2,o.return=t,l.return=t,o.sibling=l,t.child=o,(t.mode&1)!==0&&_l(t,e.child,null,i),t.child.memoizedState=md(i),t.memoizedState=pd,l);if((t.mode&1)===0)return ws(e,t,i,null);if(r.data==="$!"){if(o=r.nextSibling&&r.nextSibling.dataset,o)var s=o.dgst;return o=s,l=Error(H(419)),o=Nc(l,o,void 0),ws(e,t,i,o)}if(s=(i&e.childLanes)!==0,fn||s){if(o=Ht,o!==null){switch(i&-i){case 4:r=2;break;case 16:r=8;break;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:r=32;break;case 536870912:r=268435456;break;default:r=0}r=(r&(o.suspendedLanes|i))!==0?0:r,r!==0&&r!==l.retryLane&&(l.retryLane=r,Lo(e,r),Gn(o,e,r,-1))}return du(),o=Nc(Error(H(421))),ws(e,t,i,o)}return r.data==="$?"?(t.flags|=128,t.child=e.child,t=jg.bind(null,e),r._reactRetry=t,null):(e=l.treeContext,xn=Qo(r.nextSibling),vn=t,gt=!0,Kn=null,e!==null&&(Rn[Pn++]=ko,Rn[Pn++]=Co,Rn[Pn++]=wr,ko=e.id,Co=e.overflow,wr=t),t=ru(t,o.children),t.flags|=4096,t)}function T0(e,t,n){e.lanes|=t;var o=e.alternate;o!==null&&(o.lanes|=t),cd(e.return,t,n)}function $c(e,t,n,o,r){var l=e.memoizedState;l===null?e.memoizedState={isBackwards:t,rendering:null,renderingStartTime:0,last:o,tail:n,tailMode:r}:(l.isBackwards=t,l.rendering=null,l.renderingStartTime=0,l.last=o,l.tail=n,l.tailMode=r)}function kh(e,t,n){var o=t.pendingProps,r=o.revealOrder,l=o.tail;if(on(e,t,o.children,n),o=wt.current,(o&2)!==0)o=o&1|2,t.flags|=128;else{if(e!==null&&(e.flags&128)!==0)e:for(e=t.child;e!==null;){if(e.tag===13)e.memoizedState!==null&&T0(e,n,t);else if(e.tag===19)T0(e,n,t);else if(e.child!==null){e.child.return=e,e=e.child;continue}if(e===t)break e;for(;e.sibling===null;){if(e.return===null||e.return===t)break e;e=e.return}e.sibling.return=e.return,e=e.sibling}o&=1}if(ht(wt,o),(t.mode&1)===0)t.memoizedState=null;else switch(r){case"forwards":for(n=t.child,r=null;n!==null;)e=n.alternate,e!==null&&qs(e)===null&&(r=n),n=n.sibling;n=r,n===null?(r=t.child,t.child=null):(r=n.sibling,n.sibling=null),$c(t,!1,r,n,l);break;case"backwards":for(n=null,r=t.child,t.child=null;r!==null;){if(e=r.alternate,e!==null&&qs(e)===null){t.child=r;break}e=r.sibling,r.sibling=n,n=r,r=e}$c(t,!0,n,null,l);break;case"together":$c(t,!1,null,null,void 0);break;default:t.memoizedState=null}return t.child}function Ns(e,t){(t.mode&1)===0&&e!==null&&(e.alternate=null,t.alternate=null,t.flags|=2)}function Io(e,t,n){if(e!==null&&(t.dependencies=e.dependencies),kr|=t.lanes,(n&t.childLanes)===0)return null;if(e!==null&&t.child!==e.child)throw Error(H(153));if(t.child!==null){for(e=t.child,n=Go(e,e.pendingProps),t.child=n,n.return=t;e.sibling!==null;)e=e.sibling,n=n.sibling=Go(e,e.pendingProps),n.return=t;n.sibling=null}return t.child}function Ng(e,t,n){switch(t.tag){case 3:wh(t),ul();break;case 5:Kf(t);break;case 1:pn(t.type)&&Us(t);break;case 4:qd(t,t.stateNode.containerInfo);break;case 10:var o=t.type._context,r=t.memoizedProps.value;ht(Qs,o._currentValue),o._currentValue=r;break;case 13:if(o=t.memoizedState,o!==null)return o.dehydrated!==null?(ht(wt,wt.current&1),t.flags|=128,null):(n&t.child.childLanes)!==0?bh(e,t,n):(ht(wt,wt.current&1),e=Io(e,t,n),e!==null?e.sibling:null);ht(wt,wt.current&1);break;case 19:if(o=(n&t.childLanes)!==0,(e.flags&128)!==0){if(o)return kh(e,t,n);t.flags|=128}if(r=t.memoizedState,r!==null&&(r.rendering=null,r.tail=null,r.lastEffect=null),ht(wt,wt.current),o)break;return null;case 22:case 23:return t.lanes=0,xh(e,t,n)}return Io(e,t,n)}var Ch,gd,Sh,Mh;Ch=function(e,t){for(var n=t.child;n!==null;){if(n.tag===5||n.tag===6)e.appendChild(n.stateNode);else if(n.tag!==4&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return;n=n.return}n.sibling.return=n.return,n=n.sibling}};gd=function(){};Sh=function(e,t,n,o){var r=e.memoizedProps;if(r!==o){e=t.stateNode,gr(fo.current);var l=null;switch(n){case"input":r=Ac(e,r),o=Ac(e,o),l=[];break;case"select":r=kt({},r,{value:void 0}),o=kt({},o,{value:void 0}),l=[];break;case"textarea":r=jc(e,r),o=jc(e,o),l=[];break;default:typeof r.onClick!="function"&&typeof o.onClick=="function"&&(e.onclick=js)}Uc(n,o);var i;n=null;for(m in r)if(!o.hasOwnProperty(m)&&r.hasOwnProperty(m)&&r[m]!=null)if(m==="style"){var s=r[m];for(i in s)s.hasOwnProperty(i)&&(n||(n={}),n[i]="")}else m!=="dangerouslySetInnerHTML"&&m!=="children"&&m!=="suppressContentEditableWarning"&&m!=="suppressHydrationWarning"&&m!=="autoFocus"&&(ci.hasOwnProperty(m)?l||(l=[]):(l=l||[]).push(m,null));for(m in o){var a=o[m];if(s=r?.[m],o.hasOwnProperty(m)&&a!==s&&(a!=null||s!=null))if(m==="style")if(s){for(i in s)!s.hasOwnProperty(i)||a&&a.hasOwnProperty(i)||(n||(n={}),n[i]="");for(i in a)a.hasOwnProperty(i)&&s[i]!==a[i]&&(n||(n={}),n[i]=a[i])}else n||(l||(l=[]),l.push(m,n)),n=a;else m==="dangerouslySetInnerHTML"?(a=a?a.__html:void 0,s=s?s.__html:void 0,a!=null&&s!==a&&(l=l||[]).push(m,a)):m==="children"?typeof a!="string"&&typeof a!="number"||(l=l||[]).push(m,""+a):m!=="suppressContentEditableWarning"&&m!=="suppressHydrationWarning"&&(ci.hasOwnProperty(m)?(a!=null&&m==="onScroll"&&pt("scroll",e),l||s===a||(l=[])):(l=l||[]).push(m,a))}n&&(l=l||[]).push("style",n);var m=l;(t.updateQueue=m)&&(t.flags|=4)}};Mh=function(e,t,n,o){n!==o&&(t.flags|=4)};function Ql(e,t){if(!gt)switch(e.tailMode){case"hidden":t=e.tail;for(var n=null;t!==null;)t.alternate!==null&&(n=t),t=t.sibling;n===null?e.tail=null:n.sibling=null;break;case"collapsed":n=e.tail;for(var o=null;n!==null;)n.alternate!==null&&(o=n),n=n.sibling;o===null?t||e.tail===null?e.tail=null:e.tail.sibling=null:o.sibling=null}}function Gt(e){var t=e.alternate!==null&&e.alternate.child===e.child,n=0,o=0;if(t)for(var r=e.child;r!==null;)n|=r.lanes|r.childLanes,o|=r.subtreeFlags&14680064,o|=r.flags&14680064,r.return=e,r=r.sibling;else for(r=e.child;r!==null;)n|=r.lanes|r.childLanes,o|=r.subtreeFlags,o|=r.flags,r.return=e,r=r.sibling;return e.subtreeFlags|=o,e.childLanes=n,t}function $g(e,t,n){var o=t.pendingProps;switch(Hd(t),t.tag){case 2:case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return Gt(t),null;case 1:return pn(t.type)&&Hs(),Gt(t),null;case 3:return o=t.stateNode,fl(),mt(hn),mt(Jt),Zd(),o.pendingContext&&(o.context=o.pendingContext,o.pendingContext=null),(e===null||e.child===null)&&(xs(t)?t.flags|=4:e===null||e.memoizedState.isDehydrated&&(t.flags&256)===0||(t.flags|=1024,Kn!==null&&(Sd(Kn),Kn=null))),gd(e,t),Gt(t),null;case 5:Gd(t);var r=gr(wi.current);if(n=t.type,e!==null&&t.stateNode!=null)Sh(e,t,n,o,r),e.ref!==t.ref&&(t.flags|=512,t.flags|=2097152);else{if(!o){if(t.stateNode===null)throw Error(H(166));return Gt(t),null}if(e=gr(fo.current),xs(t)){o=t.stateNode,n=t.type;var l=t.memoizedProps;switch(o[uo]=t,o[xi]=l,e=(t.mode&1)!==0,n){case"dialog":pt("cancel",o),pt("close",o);break;case"iframe":case"object":case"embed":pt("load",o);break;case"video":case"audio":for(r=0;r<Jl.length;r++)pt(Jl[r],o);break;case"source":pt("error",o);break;case"img":case"image":case"link":pt("error",o),pt("load",o);break;case"details":pt("toggle",o);break;case"input":j_(o,l),pt("invalid",o);break;case"select":o._wrapperState={wasMultiple:!!l.multiple},pt("invalid",o);break;case"textarea":U_(o,l),pt("invalid",o)}Uc(n,l),r=null;for(var i in l)if(l.hasOwnProperty(i)){var s=l[i];i==="children"?typeof s=="string"?o.textContent!==s&&(l.suppressHydrationWarning!==!0&&ys(o.textContent,s,e),r=["children",s]):typeof s=="number"&&o.textContent!==""+s&&(l.suppressHydrationWarning!==!0&&ys(o.textContent,s,e),r=["children",""+s]):ci.hasOwnProperty(i)&&s!=null&&i==="onScroll"&&pt("scroll",o)}switch(n){case"input":is(o),H_(o,l,!0);break;case"textarea":is(o),Y_(o);break;case"select":case"option":break;default:typeof l.onClick=="function"&&(o.onclick=js)}o=r,t.updateQueue=o,o!==null&&(t.flags|=4)}else{i=r.nodeType===9?r:r.ownerDocument,e==="http://www.w3.org/1999/xhtml"&&(e=J0(n)),e==="http://www.w3.org/1999/xhtml"?n==="script"?(e=i.createElement("div"),e.innerHTML="<script><\/script>",e=e.removeChild(e.firstChild)):typeof o.is=="string"?e=i.createElement(n,{is:o.is}):(e=i.createElement(n),n==="select"&&(i=e,o.multiple?i.multiple=!0:o.size&&(i.size=o.size))):e=i.createElementNS(e,n),e[uo]=t,e[xi]=o,Ch(e,t,!1,!1),t.stateNode=e;e:{switch(i=Yc(n,o),n){case"dialog":pt("cancel",e),pt("close",e),r=o;break;case"iframe":case"object":case"embed":pt("load",e),r=o;break;case"video":case"audio":for(r=0;r<Jl.length;r++)pt(Jl[r],e);r=o;break;case"source":pt("error",e),r=o;break;case"img":case"image":case"link":pt("error",e),pt("load",e),r=o;break;case"details":pt("toggle",e),r=o;break;case"input":j_(e,o),r=Ac(e,o),pt("invalid",e);break;case"option":r=o;break;case"select":e._wrapperState={wasMultiple:!!o.multiple},r=kt({},o,{value:void 0}),pt("invalid",e);break;case"textarea":U_(e,o),r=jc(e,o),pt("invalid",e);break;default:r=o}Uc(n,r),s=r;for(l in s)if(s.hasOwnProperty(l)){var a=s[l];l==="style"?nf(e,a):l==="dangerouslySetInnerHTML"?(a=a?a.__html:void 0,a!=null&&ef(e,a)):l==="children"?typeof a=="string"?(n!=="textarea"||a!=="")&&di(e,a):typeof a=="number"&&di(e,""+a):l!=="suppressContentEditableWarning"&&l!=="suppressHydrationWarning"&&l!=="autoFocus"&&(ci.hasOwnProperty(l)?a!=null&&l==="onScroll"&&pt("scroll",e):a!=null&&Ld(e,l,a,i))}switch(n){case"input":is(e),H_(e,o,!1);break;case"textarea":is(e),Y_(e);break;case"option":o.value!=null&&e.setAttribute("value",""+Zo(o.value));break;case"select":e.multiple=!!o.multiple,l=o.value,l!=null?ol(e,!!o.multiple,l,!1):o.defaultValue!=null&&ol(e,!!o.multiple,o.defaultValue,!0);break;default:typeof r.onClick=="function"&&(e.onclick=js)}switch(n){case"button":case"input":case"select":case"textarea":o=!!o.autoFocus;break e;case"img":o=!0;break e;default:o=!1}}o&&(t.flags|=4)}t.ref!==null&&(t.flags|=512,t.flags|=2097152)}return Gt(t),null;case 6:if(e&&t.stateNode!=null)Mh(e,t,e.memoizedProps,o);else{if(typeof o!="string"&&t.stateNode===null)throw Error(H(166));if(n=gr(wi.current),gr(fo.current),xs(t)){if(o=t.stateNode,n=t.memoizedProps,o[uo]=t,(l=o.nodeValue!==n)&&(e=vn,e!==null))switch(e.tag){case 3:ys(o.nodeValue,n,(e.mode&1)!==0);break;case 5:e.memoizedProps.suppressHydrationWarning!==!0&&ys(o.nodeValue,n,(e.mode&1)!==0)}l&&(t.flags|=4)}else o=(n.nodeType===9?n:n.ownerDocument).createTextNode(o),o[uo]=t,t.stateNode=o}return Gt(t),null;case 13:if(mt(wt),o=t.memoizedState,e===null||e.memoizedState!==null&&e.memoizedState.dehydrated!==null){if(gt&&xn!==null&&(t.mode&1)!==0&&(t.flags&128)===0)Uf(),ul(),t.flags|=98560,l=!1;else if(l=xs(t),o!==null&&o.dehydrated!==null){if(e===null){if(!l)throw Error(H(318));if(l=t.memoizedState,l=l!==null?l.dehydrated:null,!l)throw Error(H(317));l[uo]=t}else ul(),(t.flags&128)===0&&(t.memoizedState=null),t.flags|=4;Gt(t),l=!1}else Kn!==null&&(Sd(Kn),Kn=null),l=!0;if(!l)return t.flags&65536?t:null}return(t.flags&128)!==0?(t.lanes=n,t):(o=o!==null,o!==(e!==null&&e.memoizedState!==null)&&o&&(t.child.flags|=8192,(t.mode&1)!==0&&(e===null||(wt.current&1)!==0?Wt===0&&(Wt=3):du())),t.updateQueue!==null&&(t.flags|=4),Gt(t),null);case 4:return fl(),gd(e,t),e===null&&gi(t.stateNode.containerInfo),Gt(t),null;case 10:return Qd(t.type._context),Gt(t),null;case 17:return pn(t.type)&&Hs(),Gt(t),null;case 19:if(mt(wt),l=t.memoizedState,l===null)return Gt(t),null;if(o=(t.flags&128)!==0,i=l.rendering,i===null)if(o)Ql(l,!1);else{if(Wt!==0||e!==null&&(e.flags&128)!==0)for(e=t.child;e!==null;){if(i=qs(e),i!==null){for(t.flags|=128,Ql(l,!1),o=i.updateQueue,o!==null&&(t.updateQueue=o,t.flags|=4),t.subtreeFlags=0,o=n,n=t.child;n!==null;)l=n,e=o,l.flags&=14680066,i=l.alternate,i===null?(l.childLanes=0,l.lanes=e,l.child=null,l.subtreeFlags=0,l.memoizedProps=null,l.memoizedState=null,l.updateQueue=null,l.dependencies=null,l.stateNode=null):(l.childLanes=i.childLanes,l.lanes=i.lanes,l.child=i.child,l.subtreeFlags=0,l.deletions=null,l.memoizedProps=i.memoizedProps,l.memoizedState=i.memoizedState,l.updateQueue=i.updateQueue,l.type=i.type,e=i.dependencies,l.dependencies=e===null?null:{lanes:e.lanes,firstContext:e.firstContext}),n=n.sibling;return ht(wt,wt.current&1|2),t.child}e=e.sibling}l.tail!==null&&Rt()>pl&&(t.flags|=128,o=!0,Ql(l,!1),t.lanes=4194304)}else{if(!o)if(e=qs(i),e!==null){if(t.flags|=128,o=!0,n=e.updateQueue,n!==null&&(t.updateQueue=n,t.flags|=4),Ql(l,!0),l.tail===null&&l.tailMode==="hidden"&&!i.alternate&&!gt)return Gt(t),null}else 2*Rt()-l.renderingStartTime>pl&&n!==1073741824&&(t.flags|=128,o=!0,Ql(l,!1),t.lanes=4194304);l.isBackwards?(i.sibling=t.child,t.child=i):(n=l.last,n!==null?n.sibling=i:t.child=i,l.last=i)}return l.tail!==null?(t=l.tail,l.rendering=t,l.tail=t.sibling,l.renderingStartTime=Rt(),t.sibling=null,n=wt.current,ht(wt,o?n&1|2:n&1),t):(Gt(t),null);case 22:case 23:return cu(),o=t.memoizedState!==null,e!==null&&e.memoizedState!==null!==o&&(t.flags|=8192),o&&(t.mode&1)!==0?(yn&1073741824)!==0&&(Gt(t),t.subtreeFlags&6&&(t.flags|=8192)):Gt(t),null;case 24:return null;case 25:return null}throw Error(H(156,t.tag))}function Rg(e,t){switch(Hd(t),t.tag){case 1:return pn(t.type)&&Hs(),e=t.flags,e&65536?(t.flags=e&-65537|128,t):null;case 3:return fl(),mt(hn),mt(Jt),Zd(),e=t.flags,(e&65536)!==0&&(e&128)===0?(t.flags=e&-65537|128,t):null;case 5:return Gd(t),null;case 13:if(mt(wt),e=t.memoizedState,e!==null&&e.dehydrated!==null){if(t.alternate===null)throw Error(H(340));ul()}return e=t.flags,e&65536?(t.flags=e&-65537|128,t):null;case 19:return mt(wt),null;case 4:return fl(),null;case 10:return Qd(t.type._context),null;case 22:case 23:return cu(),null;case 24:return null;default:return null}}var bs=!1,Zt=!1,Pg=typeof WeakSet=="function"?WeakSet:Set,ne=null;function tl(e,t){var n=e.ref;if(n!==null)if(typeof n=="function")try{n(null)}catch(o){Lt(e,t,o)}else n.current=null}function yd(e,t,n){try{n()}catch(o){Lt(e,t,o)}}var D0=!1;function Tg(e,t){if(td=As,e=$f(),Fd(e)){if("selectionStart"in e)var n={start:e.selectionStart,end:e.selectionEnd};else e:{n=(n=e.ownerDocument)&&n.defaultView||window;var o=n.getSelection&&n.getSelection();if(o&&o.rangeCount!==0){n=o.anchorNode;var r=o.anchorOffset,l=o.focusNode;o=o.focusOffset;try{n.nodeType,l.nodeType}catch{n=null;break e}var i=0,s=-1,a=-1,m=0,p=0,b=e,y=null;t:for(;;){for(var R;b!==n||r!==0&&b.nodeType!==3||(s=i+r),b!==l||o!==0&&b.nodeType!==3||(a=i+o),b.nodeType===3&&(i+=b.nodeValue.length),(R=b.firstChild)!==null;)y=b,b=R;for(;;){if(b===e)break t;if(y===n&&++m===r&&(s=i),y===l&&++p===o&&(a=i),(R=b.nextSibling)!==null)break;b=y,y=b.parentNode}b=R}n=s===-1||a===-1?null:{start:s,end:a}}else n=null}n=n||{start:0,end:0}}else n=null;for(nd={focusedElem:e,selectionRange:n},As=!1,ne=t;ne!==null;)if(t=ne,e=t.child,(t.subtreeFlags&1028)!==0&&e!==null)e.return=t,ne=e;else for(;ne!==null;){t=ne;try{var C=t.alternate;if((t.flags&1024)!==0)switch(t.tag){case 0:case 11:case 15:break;case 1:if(C!==null){var N=C.memoizedProps,L=C.memoizedState,f=t.stateNode,g=f.getSnapshotBeforeUpdate(t.elementType===t.type?N:Qn(t.type,N),L);f.__reactInternalSnapshotBeforeUpdate=g}break;case 3:var w=t.stateNode.containerInfo;w.nodeType===1?w.textContent="":w.nodeType===9&&w.documentElement&&w.removeChild(w.documentElement);break;case 5:case 6:case 4:case 17:break;default:throw Error(H(163))}}catch($){Lt(t,t.return,$)}if(e=t.sibling,e!==null){e.return=t.return,ne=e;break}ne=t.return}return C=D0,D0=!1,C}function ii(e,t,n){var o=t.updateQueue;if(o=o!==null?o.lastEffect:null,o!==null){var r=o=o.next;do{if((r.tag&e)===e){var l=r.destroy;r.destroy=void 0,l!==void 0&&yd(t,n,l)}r=r.next}while(r!==o)}}function _a(e,t){if(t=t.updateQueue,t=t!==null?t.lastEffect:null,t!==null){var n=t=t.next;do{if((n.tag&e)===e){var o=n.create;n.destroy=o()}n=n.next}while(n!==t)}}function xd(e){var t=e.ref;if(t!==null){var n=e.stateNode;switch(e.tag){case 5:e=n;break;default:e=n}typeof t=="function"?t(e):t.current=e}}function Eh(e){var t=e.alternate;t!==null&&(e.alternate=null,Eh(t)),e.child=null,e.deletions=null,e.sibling=null,e.tag===5&&(t=e.stateNode,t!==null&&(delete t[uo],delete t[xi],delete t[ld],delete t[mg],delete t[gg])),e.stateNode=null,e.return=null,e.dependencies=null,e.memoizedProps=null,e.memoizedState=null,e.pendingProps=null,e.stateNode=null,e.updateQueue=null}function Lh(e){return e.tag===5||e.tag===3||e.tag===4}function B0(e){e:for(;;){for(;e.sibling===null;){if(e.return===null||Lh(e.return))return null;e=e.return}for(e.sibling.return=e.return,e=e.sibling;e.tag!==5&&e.tag!==6&&e.tag!==18;){if(e.flags&2||e.child===null||e.tag===4)continue e;e.child.return=e,e=e.child}if(!(e.flags&2))return e.stateNode}}function vd(e,t,n){var o=e.tag;if(o===5||o===6)e=e.stateNode,t?n.nodeType===8?n.parentNode.insertBefore(e,t):n.insertBefore(e,t):(n.nodeType===8?(t=n.parentNode,t.insertBefore(e,n)):(t=n,t.appendChild(e)),n=n._reactRootContainer,n!=null||t.onclick!==null||(t.onclick=js));else if(o!==4&&(e=e.child,e!==null))for(vd(e,t,n),e=e.sibling;e!==null;)vd(e,t,n),e=e.sibling}function wd(e,t,n){var o=e.tag;if(o===5||o===6)e=e.stateNode,t?n.insertBefore(e,t):n.appendChild(e);else if(o!==4&&(e=e.child,e!==null))for(wd(e,t,n),e=e.sibling;e!==null;)wd(e,t,n),e=e.sibling}var Yt=null,Vn=!1;function zo(e,t,n){for(n=n.child;n!==null;)Ih(e,t,n),n=n.sibling}function Ih(e,t,n){if(_o&&typeof _o.onCommitFiberUnmount=="function")try{_o.onCommitFiberUnmount(ra,n)}catch{}switch(n.tag){case 5:Zt||tl(n,t);case 6:var o=Yt,r=Vn;Yt=null,zo(e,t,n),Yt=o,Vn=r,Yt!==null&&(Vn?(e=Yt,n=n.stateNode,e.nodeType===8?e.parentNode.removeChild(n):e.removeChild(n)):Yt.removeChild(n.stateNode));break;case 18:Yt!==null&&(Vn?(e=Yt,n=n.stateNode,e.nodeType===8?Cc(e.parentNode,n):e.nodeType===1&&Cc(e,n),hi(e)):Cc(Yt,n.stateNode));break;case 4:o=Yt,r=Vn,Yt=n.stateNode.containerInfo,Vn=!0,zo(e,t,n),Yt=o,Vn=r;break;case 0:case 11:case 14:case 15:if(!Zt&&(o=n.updateQueue,o!==null&&(o=o.lastEffect,o!==null))){r=o=o.next;do{var l=r,i=l.destroy;l=l.tag,i!==void 0&&((l&2)!==0||(l&4)!==0)&&yd(n,t,i),r=r.next}while(r!==o)}zo(e,t,n);break;case 1:if(!Zt&&(tl(n,t),o=n.stateNode,typeof o.componentWillUnmount=="function"))try{o.props=n.memoizedProps,o.state=n.memoizedState,o.componentWillUnmount()}catch(s){Lt(n,t,s)}zo(e,t,n);break;case 21:zo(e,t,n);break;case 22:n.mode&1?(Zt=(o=Zt)||n.memoizedState!==null,zo(e,t,n),Zt=o):zo(e,t,n);break;default:zo(e,t,n)}}function z0(e){var t=e.updateQueue;if(t!==null){e.updateQueue=null;var n=e.stateNode;n===null&&(n=e.stateNode=new Pg),t.forEach(function(o){var r=Hg.bind(null,e,o);n.has(o)||(n.add(o),o.then(r,r))})}}function Xn(e,t){var n=t.deletions;if(n!==null)for(var o=0;o<n.length;o++){var r=n[o];try{var l=e,i=t,s=i;e:for(;s!==null;){switch(s.tag){case 5:Yt=s.stateNode,Vn=!1;break e;case 3:Yt=s.stateNode.containerInfo,Vn=!0;break e;case 4:Yt=s.stateNode.containerInfo,Vn=!0;break e}s=s.return}if(Yt===null)throw Error(H(160));Ih(l,i,r),Yt=null,Vn=!1;var a=r.alternate;a!==null&&(a.return=null),r.return=null}catch(m){Lt(r,t,m)}}if(t.subtreeFlags&12854)for(t=t.child;t!==null;)Nh(t,e),t=t.sibling}function Nh(e,t){var n=e.alternate,o=e.flags;switch(e.tag){case 0:case 11:case 14:case 15:if(Xn(t,e),ao(e),o&4){try{ii(3,e,e.return),_a(3,e)}catch(N){Lt(e,e.return,N)}try{ii(5,e,e.return)}catch(N){Lt(e,e.return,N)}}break;case 1:Xn(t,e),ao(e),o&512&&n!==null&&tl(n,n.return);break;case 5:if(Xn(t,e),ao(e),o&512&&n!==null&&tl(n,n.return),e.flags&32){var r=e.stateNode;try{di(r,"")}catch(N){Lt(e,e.return,N)}}if(o&4&&(r=e.stateNode,r!=null)){var l=e.memoizedProps,i=n!==null?n.memoizedProps:l,s=e.type,a=e.updateQueue;if(e.updateQueue=null,a!==null)try{s==="input"&&l.type==="radio"&&l.name!=null&&G0(r,l),Yc(s,i);var m=Yc(s,l);for(i=0;i<a.length;i+=2){var p=a[i],b=a[i+1];p==="style"?nf(r,b):p==="dangerouslySetInnerHTML"?ef(r,b):p==="children"?di(r,b):Ld(r,p,b,m)}switch(s){case"input":Wc(r,l);break;case"textarea":Z0(r,l);break;case"select":var y=r._wrapperState.wasMultiple;r._wrapperState.wasMultiple=!!l.multiple;var R=l.value;R!=null?ol(r,!!l.multiple,R,!1):y!==!!l.multiple&&(l.defaultValue!=null?ol(r,!!l.multiple,l.defaultValue,!0):ol(r,!!l.multiple,l.multiple?[]:"",!1))}r[xi]=l}catch(N){Lt(e,e.return,N)}}break;case 6:if(Xn(t,e),ao(e),o&4){if(e.stateNode===null)throw Error(H(162));r=e.stateNode,l=e.memoizedProps;try{r.nodeValue=l}catch(N){Lt(e,e.return,N)}}break;case 3:if(Xn(t,e),ao(e),o&4&&n!==null&&n.memoizedState.isDehydrated)try{hi(t.containerInfo)}catch(N){Lt(e,e.return,N)}break;case 4:Xn(t,e),ao(e);break;case 13:Xn(t,e),ao(e),r=e.child,r.flags&8192&&(l=r.memoizedState!==null,r.stateNode.isHidden=l,!l||r.alternate!==null&&r.alternate.memoizedState!==null||(su=Rt())),o&4&&z0(e);break;case 22:if(p=n!==null&&n.memoizedState!==null,e.mode&1?(Zt=(m=Zt)||p,Xn(t,e),Zt=m):Xn(t,e),ao(e),o&8192){if(m=e.memoizedState!==null,(e.stateNode.isHidden=m)&&!p&&(e.mode&1)!==0)for(ne=e,p=e.child;p!==null;){for(b=ne=p;ne!==null;){switch(y=ne,R=y.child,y.tag){case 0:case 11:case 14:case 15:ii(4,y,y.return);break;case 1:tl(y,y.return);var C=y.stateNode;if(typeof C.componentWillUnmount=="function"){o=y,n=y.return;try{t=o,C.props=t.memoizedProps,C.state=t.memoizedState,C.componentWillUnmount()}catch(N){Lt(o,n,N)}}break;case 5:tl(y,y.return);break;case 22:if(y.memoizedState!==null){A0(b);continue}}R!==null?(R.return=y,ne=R):A0(b)}p=p.sibling}e:for(p=null,b=e;;){if(b.tag===5){if(p===null){p=b;try{r=b.stateNode,m?(l=r.style,typeof l.setProperty=="function"?l.setProperty("display","none","important"):l.display="none"):(s=b.stateNode,a=b.memoizedProps.style,i=a!=null&&a.hasOwnProperty("display")?a.display:null,s.style.display=tf("display",i))}catch(N){Lt(e,e.return,N)}}}else if(b.tag===6){if(p===null)try{b.stateNode.nodeValue=m?"":b.memoizedProps}catch(N){Lt(e,e.return,N)}}else if((b.tag!==22&&b.tag!==23||b.memoizedState===null||b===e)&&b.child!==null){b.child.return=b,b=b.child;continue}if(b===e)break e;for(;b.sibling===null;){if(b.return===null||b.return===e)break e;p===b&&(p=null),b=b.return}p===b&&(p=null),b.sibling.return=b.return,b=b.sibling}}break;case 19:Xn(t,e),ao(e),o&4&&z0(e);break;case 21:break;default:Xn(t,e),ao(e)}}function ao(e){var t=e.flags;if(t&2){try{e:{for(var n=e.return;n!==null;){if(Lh(n)){var o=n;break e}n=n.return}throw Error(H(160))}switch(o.tag){case 5:var r=o.stateNode;o.flags&32&&(di(r,""),o.flags&=-33);var l=B0(e);wd(e,l,r);break;case 3:case 4:var i=o.stateNode.containerInfo,s=B0(e);vd(e,s,i);break;default:throw Error(H(161))}}catch(a){Lt(e,e.return,a)}e.flags&=-3}t&4096&&(e.flags&=-4097)}function Dg(e,t,n){ne=e,$h(e,t,n)}function $h(e,t,n){for(var o=(e.mode&1)!==0;ne!==null;){var r=ne,l=r.child;if(r.tag===22&&o){var i=r.memoizedState!==null||bs;if(!i){var s=r.alternate,a=s!==null&&s.memoizedState!==null||Zt;s=bs;var m=Zt;if(bs=i,(Zt=a)&&!m)for(ne=r;ne!==null;)i=ne,a=i.child,i.tag===22&&i.memoizedState!==null?W0(r):a!==null?(a.return=i,ne=a):W0(r);for(;l!==null;)ne=l,$h(l,t,n),l=l.sibling;ne=r,bs=s,Zt=m}O0(e,t,n)}else(r.subtreeFlags&8772)!==0&&l!==null?(l.return=r,ne=l):O0(e,t,n)}}function O0(e){for(;ne!==null;){var t=ne;if((t.flags&8772)!==0){var n=t.alternate;try{if((t.flags&8772)!==0)switch(t.tag){case 0:case 11:case 15:Zt||_a(5,t);break;case 1:var o=t.stateNode;if(t.flags&4&&!Zt)if(n===null)o.componentDidMount();else{var r=t.elementType===t.type?n.memoizedProps:Qn(t.type,n.memoizedProps);o.componentDidUpdate(r,n.memoizedState,o.__reactInternalSnapshotBeforeUpdate)}var l=t.updateQueue;l!==null&&b0(t,l,o);break;case 3:var i=t.updateQueue;if(i!==null){if(n=null,t.child!==null)switch(t.child.tag){case 5:n=t.child.stateNode;break;case 1:n=t.child.stateNode}b0(t,i,n)}break;case 5:var s=t.stateNode;if(n===null&&t.flags&4){n=s;var a=t.memoizedProps;switch(t.type){case"button":case"input":case"select":case"textarea":a.autoFocus&&n.focus();break;case"img":a.src&&(n.src=a.src)}}break;case 6:break;case 4:break;case 12:break;case 13:if(t.memoizedState===null){var m=t.alternate;if(m!==null){var p=m.memoizedState;if(p!==null){var b=p.dehydrated;b!==null&&hi(b)}}}break;case 19:case 17:case 21:case 22:case 23:case 25:break;default:throw Error(H(163))}Zt||t.flags&512&&xd(t)}catch(y){Lt(t,t.return,y)}}if(t===e){ne=null;break}if(n=t.sibling,n!==null){n.return=t.return,ne=n;break}ne=t.return}}function A0(e){for(;ne!==null;){var t=ne;if(t===e){ne=null;break}var n=t.sibling;if(n!==null){n.return=t.return,ne=n;break}ne=t.return}}function W0(e){for(;ne!==null;){var t=ne;try{switch(t.tag){case 0:case 11:case 15:var n=t.return;try{_a(4,t)}catch(a){Lt(t,n,a)}break;case 1:var o=t.stateNode;if(typeof o.componentDidMount=="function"){var r=t.return;try{o.componentDidMount()}catch(a){Lt(t,r,a)}}var l=t.return;try{xd(t)}catch(a){Lt(t,l,a)}break;case 5:var i=t.return;try{xd(t)}catch(a){Lt(t,i,a)}}}catch(a){Lt(t,t.return,a)}if(t===e){ne=null;break}var s=t.sibling;if(s!==null){s.return=t.return,ne=s;break}ne=t.return}}var Bg=Math.ceil,Js=No.ReactCurrentDispatcher,lu=No.ReactCurrentOwner,Dn=No.ReactCurrentBatchConfig,Ve=0,Ht=null,Bt=null,Xt=0,yn=0,nl=tr(0),Wt=0,Si=null,kr=0,fa=0,iu=0,si=null,_n=null,su=0,pl=1/0,wo=null,ea=!1,bd=null,Ko=null,ks=!1,Ho=null,ta=0,ai=0,kd=null,$s=-1,Rs=0;function rn(){return(Ve&6)!==0?Rt():$s!==-1?$s:$s=Rt()}function qo(e){return(e.mode&1)===0?1:(Ve&2)!==0&&Xt!==0?Xt&-Xt:xg.transition!==null?(Rs===0&&(Rs=pf()),Rs):(e=lt,e!==0||(e=window.event,e=e===void 0?16:bf(e.type)),e)}function Gn(e,t,n,o){if(50<ai)throw ai=0,kd=null,Error(H(185));Mi(e,n,o),((Ve&2)===0||e!==Ht)&&(e===Ht&&((Ve&2)===0&&(fa|=n),Wt===4&&Fo(e,Xt)),mn(e,o),n===1&&Ve===0&&(t.mode&1)===0&&(pl=Rt()+500,ca&&nr()))}function mn(e,t){var n=e.callbackNode;w1(e,t);var o=Os(e,e===Ht?Xt:0);if(o===0)n!==null&&V_(n),e.callbackNode=null,e.callbackPriority=0;else if(t=o&-o,e.callbackPriority!==t){if(n!=null&&V_(n),t===1)e.tag===0?yg(F0.bind(null,e)):Ff(F0.bind(null,e)),hg(function(){(Ve&6)===0&&nr()}),n=null;else{switch(mf(o)){case 1:n=Pd;break;case 4:n=ff;break;case 16:n=zs;break;case 536870912:n=hf;break;default:n=zs}n=Ah(n,Rh.bind(null,e))}e.callbackPriority=t,e.callbackNode=n}}function Rh(e,t){if($s=-1,Rs=0,(Ve&6)!==0)throw Error(H(327));var n=e.callbackNode;if(al()&&e.callbackNode!==n)return null;var o=Os(e,e===Ht?Xt:0);if(o===0)return null;if((o&30)!==0||(o&e.expiredLanes)!==0||t)t=na(e,o);else{t=o;var r=Ve;Ve|=2;var l=Th();(Ht!==e||Xt!==t)&&(wo=null,pl=Rt()+500,yr(e,t));do try{Ag();break}catch(s){Ph(e,s)}while(!0);Xd(),Js.current=l,Ve=r,Bt!==null?t=0:(Ht=null,Xt=0,t=Wt)}if(t!==0){if(t===2&&(r=qc(e),r!==0&&(o=r,t=Cd(e,r))),t===1)throw n=Si,yr(e,0),Fo(e,o),mn(e,Rt()),n;if(t===6)Fo(e,o);else{if(r=e.current.alternate,(o&30)===0&&!zg(r)&&(t=na(e,o),t===2&&(l=qc(e),l!==0&&(o=l,t=Cd(e,l))),t===1))throw n=Si,yr(e,0),Fo(e,o),mn(e,Rt()),n;switch(e.finishedWork=r,e.finishedLanes=o,t){case 0:case 1:throw Error(H(345));case 2:hr(e,_n,wo);break;case 3:if(Fo(e,o),(o&130023424)===o&&(t=su+500-Rt(),10<t)){if(Os(e,0)!==0)break;if(r=e.suspendedLanes,(r&o)!==o){rn(),e.pingedLanes|=e.suspendedLanes&r;break}e.timeoutHandle=rd(hr.bind(null,e,_n,wo),t);break}hr(e,_n,wo);break;case 4:if(Fo(e,o),(o&4194240)===o)break;for(t=e.eventTimes,r=-1;0<o;){var i=31-qn(o);l=1<<i,i=t[i],i>r&&(r=i),o&=~l}if(o=r,o=Rt()-o,o=(120>o?120:480>o?480:1080>o?1080:1920>o?1920:3e3>o?3e3:4320>o?4320:1960*Bg(o/1960))-o,10<o){e.timeoutHandle=rd(hr.bind(null,e,_n,wo),o);break}hr(e,_n,wo);break;case 5:hr(e,_n,wo);break;default:throw Error(H(329))}}}return mn(e,Rt()),e.callbackNode===n?Rh.bind(null,e):null}function Cd(e,t){var n=si;return e.current.memoizedState.isDehydrated&&(yr(e,t).flags|=256),e=na(e,t),e!==2&&(t=_n,_n=n,t!==null&&Sd(t)),e}function Sd(e){_n===null?_n=e:_n.push.apply(_n,e)}function zg(e){for(var t=e;;){if(t.flags&16384){var n=t.updateQueue;if(n!==null&&(n=n.stores,n!==null))for(var o=0;o<n.length;o++){var r=n[o],l=r.getSnapshot;r=r.value;try{if(!Zn(l(),r))return!1}catch{return!1}}}if(n=t.child,t.subtreeFlags&16384&&n!==null)n.return=t,t=n;else{if(t===e)break;for(;t.sibling===null;){if(t.return===null||t.return===e)return!0;t=t.return}t.sibling.return=t.return,t=t.sibling}}return!0}function Fo(e,t){for(t&=~iu,t&=~fa,e.suspendedLanes|=t,e.pingedLanes&=~t,e=e.expirationTimes;0<t;){var n=31-qn(t),o=1<<n;e[n]=-1,t&=~o}}function F0(e){if((Ve&6)!==0)throw Error(H(327));al();var t=Os(e,0);if((t&1)===0)return mn(e,Rt()),null;var n=na(e,t);if(e.tag!==0&&n===2){var o=qc(e);o!==0&&(t=o,n=Cd(e,o))}if(n===1)throw n=Si,yr(e,0),Fo(e,t),mn(e,Rt()),n;if(n===6)throw Error(H(345));return e.finishedWork=e.current.alternate,e.finishedLanes=t,hr(e,_n,wo),mn(e,Rt()),null}function au(e,t){var n=Ve;Ve|=1;try{return e(t)}finally{Ve=n,Ve===0&&(pl=Rt()+500,ca&&nr())}}function Cr(e){Ho!==null&&Ho.tag===0&&(Ve&6)===0&&al();var t=Ve;Ve|=1;var n=Dn.transition,o=lt;try{if(Dn.transition=null,lt=1,e)return e()}finally{lt=o,Dn.transition=n,Ve=t,(Ve&6)===0&&nr()}}function cu(){yn=nl.current,mt(nl)}function yr(e,t){e.finishedWork=null,e.finishedLanes=0;var n=e.timeoutHandle;if(n!==-1&&(e.timeoutHandle=-1,fg(n)),Bt!==null)for(n=Bt.return;n!==null;){var o=n;switch(Hd(o),o.tag){case 1:o=o.type.childContextTypes,o!=null&&Hs();break;case 3:fl(),mt(hn),mt(Jt),Zd();break;case 5:Gd(o);break;case 4:fl();break;case 13:mt(wt);break;case 19:mt(wt);break;case 10:Qd(o.type._context);break;case 22:case 23:cu()}n=n.return}if(Ht=e,Bt=e=Go(e.current,null),Xt=yn=t,Wt=0,Si=null,iu=fa=kr=0,_n=si=null,mr!==null){for(t=0;t<mr.length;t++)if(n=mr[t],o=n.interleaved,o!==null){n.interleaved=null;var r=o.next,l=n.pending;if(l!==null){var i=l.next;l.next=r,o.next=i}n.pending=o}mr=null}return e}function Ph(e,t){do{var n=Bt;try{if(Xd(),Ls.current=Zs,Gs){for(var o=bt.memoizedState;o!==null;){var r=o.queue;r!==null&&(r.pending=null),o=o.next}Gs=!1}if(br=0,jt=At=bt=null,li=!1,bi=0,lu.current=null,n===null||n.return===null){Wt=1,Si=t,Bt=null;break}e:{var l=e,i=n.return,s=n,a=t;if(t=Xt,s.flags|=32768,a!==null&&typeof a=="object"&&typeof a.then=="function"){var m=a,p=s,b=p.tag;if((p.mode&1)===0&&(b===0||b===11||b===15)){var y=p.alternate;y?(p.updateQueue=y.updateQueue,p.memoizedState=y.memoizedState,p.lanes=y.lanes):(p.updateQueue=null,p.memoizedState=null)}var R=L0(i);if(R!==null){R.flags&=-257,I0(R,i,s,l,t),R.mode&1&&E0(l,m,t),t=R,a=m;var C=t.updateQueue;if(C===null){var N=new Set;N.add(a),t.updateQueue=N}else C.add(a);break e}else{if((t&1)===0){E0(l,m,t),du();break e}a=Error(H(426))}}else if(gt&&s.mode&1){var L=L0(i);if(L!==null){(L.flags&65536)===0&&(L.flags|=256),I0(L,i,s,l,t),Ud(hl(a,s));break e}}l=a=hl(a,s),Wt!==4&&(Wt=2),si===null?si=[l]:si.push(l),l=i;do{switch(l.tag){case 3:l.flags|=65536,t&=-t,l.lanes|=t;var f=mh(l,a,t);w0(l,f);break e;case 1:s=a;var g=l.type,w=l.stateNode;if((l.flags&128)===0&&(typeof g.getDerivedStateFromError=="function"||w!==null&&typeof w.componentDidCatch=="function"&&(Ko===null||!Ko.has(w)))){l.flags|=65536,t&=-t,l.lanes|=t;var $=gh(l,s,t);w0(l,$);break e}}l=l.return}while(l!==null)}Bh(n)}catch(U){t=U,Bt===n&&n!==null&&(Bt=n=n.return);continue}break}while(!0)}function Th(){var e=Js.current;return Js.current=Zs,e===null?Zs:e}function du(){(Wt===0||Wt===3||Wt===2)&&(Wt=4),Ht===null||(kr&268435455)===0&&(fa&268435455)===0||Fo(Ht,Xt)}function na(e,t){var n=Ve;Ve|=2;var o=Th();(Ht!==e||Xt!==t)&&(wo=null,yr(e,t));do try{Og();break}catch(r){Ph(e,r)}while(!0);if(Xd(),Ve=n,Js.current=o,Bt!==null)throw Error(H(261));return Ht=null,Xt=0,Wt}function Og(){for(;Bt!==null;)Dh(Bt)}function Ag(){for(;Bt!==null&&!_1();)Dh(Bt)}function Dh(e){var t=Oh(e.alternate,e,yn);e.memoizedProps=e.pendingProps,t===null?Bh(e):Bt=t,lu.current=null}function Bh(e){var t=e;do{var n=t.alternate;if(e=t.return,(t.flags&32768)===0){if(n=$g(n,t,yn),n!==null){Bt=n;return}}else{if(n=Rg(n,t),n!==null){n.flags&=32767,Bt=n;return}if(e!==null)e.flags|=32768,e.subtreeFlags=0,e.deletions=null;else{Wt=6,Bt=null;return}}if(t=t.sibling,t!==null){Bt=t;return}Bt=t=e}while(t!==null);Wt===0&&(Wt=5)}function hr(e,t,n){var o=lt,r=Dn.transition;try{Dn.transition=null,lt=1,Wg(e,t,n,o)}finally{Dn.transition=r,lt=o}return null}function Wg(e,t,n,o){do al();while(Ho!==null);if((Ve&6)!==0)throw Error(H(327));n=e.finishedWork;var r=e.finishedLanes;if(n===null)return null;if(e.finishedWork=null,e.finishedLanes=0,n===e.current)throw Error(H(177));e.callbackNode=null,e.callbackPriority=0;var l=n.lanes|n.childLanes;if(b1(e,l),e===Ht&&(Bt=Ht=null,Xt=0),(n.subtreeFlags&2064)===0&&(n.flags&2064)===0||ks||(ks=!0,Ah(zs,function(){return al(),null})),l=(n.flags&15990)!==0,(n.subtreeFlags&15990)!==0||l){l=Dn.transition,Dn.transition=null;var i=lt;lt=1;var s=Ve;Ve|=4,lu.current=null,Tg(e,n),Nh(n,e),ag(nd),As=!!td,nd=td=null,e.current=n,Dg(n,e,r),f1(),Ve=s,lt=i,Dn.transition=l}else e.current=n;if(ks&&(ks=!1,Ho=e,ta=r),l=e.pendingLanes,l===0&&(Ko=null),m1(n.stateNode,o),mn(e,Rt()),t!==null)for(o=e.onRecoverableError,n=0;n<t.length;n++)r=t[n],o(r.value,{componentStack:r.stack,digest:r.digest});if(ea)throw ea=!1,e=bd,bd=null,e;return(ta&1)!==0&&e.tag!==0&&al(),l=e.pendingLanes,(l&1)!==0?e===kd?ai++:(ai=0,kd=e):ai=0,nr(),null}function al(){if(Ho!==null){var e=mf(ta),t=Dn.transition,n=lt;try{if(Dn.transition=null,lt=16>e?16:e,Ho===null)var o=!1;else{if(e=Ho,Ho=null,ta=0,(Ve&6)!==0)throw Error(H(331));var r=Ve;for(Ve|=4,ne=e.current;ne!==null;){var l=ne,i=l.child;if((ne.flags&16)!==0){var s=l.deletions;if(s!==null){for(var a=0;a<s.length;a++){var m=s[a];for(ne=m;ne!==null;){var p=ne;switch(p.tag){case 0:case 11:case 15:ii(8,p,l)}var b=p.child;if(b!==null)b.return=p,ne=b;else for(;ne!==null;){p=ne;var y=p.sibling,R=p.return;if(Eh(p),p===m){ne=null;break}if(y!==null){y.return=R,ne=y;break}ne=R}}}var C=l.alternate;if(C!==null){var N=C.child;if(N!==null){C.child=null;do{var L=N.sibling;N.sibling=null,N=L}while(N!==null)}}ne=l}}if((l.subtreeFlags&2064)!==0&&i!==null)i.return=l,ne=i;else e:for(;ne!==null;){if(l=ne,(l.flags&2048)!==0)switch(l.tag){case 0:case 11:case 15:ii(9,l,l.return)}var f=l.sibling;if(f!==null){f.return=l.return,ne=f;break e}ne=l.return}}var g=e.current;for(ne=g;ne!==null;){i=ne;var w=i.child;if((i.subtreeFlags&2064)!==0&&w!==null)w.return=i,ne=w;else e:for(i=g;ne!==null;){if(s=ne,(s.flags&2048)!==0)try{switch(s.tag){case 0:case 11:case 15:_a(9,s)}}catch(U){Lt(s,s.return,U)}if(s===i){ne=null;break e}var $=s.sibling;if($!==null){$.return=s.return,ne=$;break e}ne=s.return}}if(Ve=r,nr(),_o&&typeof _o.onPostCommitFiberRoot=="function")try{_o.onPostCommitFiberRoot(ra,e)}catch{}o=!0}return o}finally{lt=n,Dn.transition=t}}return!1}function j0(e,t,n){t=hl(n,t),t=mh(e,t,1),e=Vo(e,t,1),t=rn(),e!==null&&(Mi(e,1,t),mn(e,t))}function Lt(e,t,n){if(e.tag===3)j0(e,e,n);else for(;t!==null;){if(t.tag===3){j0(t,e,n);break}else if(t.tag===1){var o=t.stateNode;if(typeof t.type.getDerivedStateFromError=="function"||typeof o.componentDidCatch=="function"&&(Ko===null||!Ko.has(o))){e=hl(n,e),e=gh(t,e,1),t=Vo(t,e,1),e=rn(),t!==null&&(Mi(t,1,e),mn(t,e));break}}t=t.return}}function Fg(e,t,n){var o=e.pingCache;o!==null&&o.delete(t),t=rn(),e.pingedLanes|=e.suspendedLanes&n,Ht===e&&(Xt&n)===n&&(Wt===4||Wt===3&&(Xt&130023424)===Xt&&500>Rt()-su?yr(e,0):iu|=n),mn(e,t)}function zh(e,t){t===0&&((e.mode&1)===0?t=1:(t=cs,cs<<=1,(cs&130023424)===0&&(cs=4194304)));var n=rn();e=Lo(e,t),e!==null&&(Mi(e,t,n),mn(e,n))}function jg(e){var t=e.memoizedState,n=0;t!==null&&(n=t.retryLane),zh(e,n)}function Hg(e,t){var n=0;switch(e.tag){case 13:var o=e.stateNode,r=e.memoizedState;r!==null&&(n=r.retryLane);break;case 19:o=e.stateNode;break;default:throw Error(H(314))}o!==null&&o.delete(t),zh(e,n)}var Oh;Oh=function(e,t,n){if(e!==null)if(e.memoizedProps!==t.pendingProps||hn.current)fn=!0;else{if((e.lanes&n)===0&&(t.flags&128)===0)return fn=!1,Ng(e,t,n);fn=(e.flags&131072)!==0}else fn=!1,gt&&(t.flags&1048576)!==0&&jf(t,Xs,t.index);switch(t.lanes=0,t.tag){case 2:var o=t.type;Ns(e,t),e=t.pendingProps;var r=dl(t,Jt.current);sl(t,n),r=eu(null,t,o,e,r,n);var l=tu();return t.flags|=1,typeof r=="object"&&r!==null&&typeof r.render=="function"&&r.$$typeof===void 0?(t.tag=1,t.memoizedState=null,t.updateQueue=null,pn(o)?(l=!0,Us(t)):l=!1,t.memoizedState=r.state!==null&&r.state!==void 0?r.state:null,Kd(t),r.updater=ua,t.stateNode=r,r._reactInternals=t,ud(t,o,e,n),t=hd(null,t,o,!0,l,n)):(t.tag=0,gt&&l&&jd(t),on(null,t,r,n),t=t.child),t;case 16:o=t.elementType;e:{switch(Ns(e,t),e=t.pendingProps,r=o._init,o=r(o._payload),t.type=o,r=t.tag=Yg(o),e=Qn(o,e),r){case 0:t=fd(null,t,o,e,n);break e;case 1:t=R0(null,t,o,e,n);break e;case 11:t=N0(null,t,o,e,n);break e;case 14:t=$0(null,t,o,Qn(o.type,e),n);break e}throw Error(H(306,o,""))}return t;case 0:return o=t.type,r=t.pendingProps,r=t.elementType===o?r:Qn(o,r),fd(e,t,o,r,n);case 1:return o=t.type,r=t.pendingProps,r=t.elementType===o?r:Qn(o,r),R0(e,t,o,r,n);case 3:e:{if(wh(t),e===null)throw Error(H(387));o=t.pendingProps,l=t.memoizedState,r=l.element,Vf(e,t),Ks(t,o,null,n);var i=t.memoizedState;if(o=i.element,l.isDehydrated)if(l={element:o,isDehydrated:!1,cache:i.cache,pendingSuspenseBoundaries:i.pendingSuspenseBoundaries,transitions:i.transitions},t.updateQueue.baseState=l,t.memoizedState=l,t.flags&256){r=hl(Error(H(423)),t),t=P0(e,t,o,n,r);break e}else if(o!==r){r=hl(Error(H(424)),t),t=P0(e,t,o,n,r);break e}else for(xn=Qo(t.stateNode.containerInfo.firstChild),vn=t,gt=!0,Kn=null,n=Xf(t,null,o,n),t.child=n;n;)n.flags=n.flags&-3|4096,n=n.sibling;else{if(ul(),o===r){t=Io(e,t,n);break e}on(e,t,o,n)}t=t.child}return t;case 5:return Kf(t),e===null&&ad(t),o=t.type,r=t.pendingProps,l=e!==null?e.memoizedProps:null,i=r.children,od(o,r)?i=null:l!==null&&od(o,l)&&(t.flags|=32),vh(e,t),on(e,t,i,n),t.child;case 6:return e===null&&ad(t),null;case 13:return bh(e,t,n);case 4:return qd(t,t.stateNode.containerInfo),o=t.pendingProps,e===null?t.child=_l(t,null,o,n):on(e,t,o,n),t.child;case 11:return o=t.type,r=t.pendingProps,r=t.elementType===o?r:Qn(o,r),N0(e,t,o,r,n);case 7:return on(e,t,t.pendingProps,n),t.child;case 8:return on(e,t,t.pendingProps.children,n),t.child;case 12:return on(e,t,t.pendingProps.children,n),t.child;case 10:e:{if(o=t.type._context,r=t.pendingProps,l=t.memoizedProps,i=r.value,ht(Qs,o._currentValue),o._currentValue=i,l!==null)if(Zn(l.value,i)){if(l.children===r.children&&!hn.current){t=Io(e,t,n);break e}}else for(l=t.child,l!==null&&(l.return=t);l!==null;){var s=l.dependencies;if(s!==null){i=l.child;for(var a=s.firstContext;a!==null;){if(a.context===o){if(l.tag===1){a=So(-1,n&-n),a.tag=2;var m=l.updateQueue;if(m!==null){m=m.shared;var p=m.pending;p===null?a.next=a:(a.next=p.next,p.next=a),m.pending=a}}l.lanes|=n,a=l.alternate,a!==null&&(a.lanes|=n),cd(l.return,n,t),s.lanes|=n;break}a=a.next}}else if(l.tag===10)i=l.type===t.type?null:l.child;else if(l.tag===18){if(i=l.return,i===null)throw Error(H(341));i.lanes|=n,s=i.alternate,s!==null&&(s.lanes|=n),cd(i,n,t),i=l.sibling}else i=l.child;if(i!==null)i.return=l;else for(i=l;i!==null;){if(i===t){i=null;break}if(l=i.sibling,l!==null){l.return=i.return,i=l;break}i=i.return}l=i}on(e,t,r.children,n),t=t.child}return t;case 9:return r=t.type,o=t.pendingProps.children,sl(t,n),r=Bn(r),o=o(r),t.flags|=1,on(e,t,o,n),t.child;case 14:return o=t.type,r=Qn(o,t.pendingProps),r=Qn(o.type,r),$0(e,t,o,r,n);case 15:return yh(e,t,t.type,t.pendingProps,n);case 17:return o=t.type,r=t.pendingProps,r=t.elementType===o?r:Qn(o,r),Ns(e,t),t.tag=1,pn(o)?(e=!0,Us(t)):e=!1,sl(t,n),ph(t,o,r),ud(t,o,r,n),hd(null,t,o,!0,e,n);case 19:return kh(e,t,n);case 22:return xh(e,t,n)}throw Error(H(156,t.tag))};function Ah(e,t){return _f(e,t)}function Ug(e,t,n,o){this.tag=e,this.key=n,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.ref=null,this.pendingProps=t,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=o,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function Tn(e,t,n,o){return new Ug(e,t,n,o)}function uu(e){return e=e.prototype,!(!e||!e.isReactComponent)}function Yg(e){if(typeof e=="function")return uu(e)?1:0;if(e!=null){if(e=e.$$typeof,e===Nd)return 11;if(e===$d)return 14}return 2}function Go(e,t){var n=e.alternate;return n===null?(n=Tn(e.tag,t,e.key,e.mode),n.elementType=e.elementType,n.type=e.type,n.stateNode=e.stateNode,n.alternate=e,e.alternate=n):(n.pendingProps=t,n.type=e.type,n.flags=0,n.subtreeFlags=0,n.deletions=null),n.flags=e.flags&14680064,n.childLanes=e.childLanes,n.lanes=e.lanes,n.child=e.child,n.memoizedProps=e.memoizedProps,n.memoizedState=e.memoizedState,n.updateQueue=e.updateQueue,t=e.dependencies,n.dependencies=t===null?null:{lanes:t.lanes,firstContext:t.firstContext},n.sibling=e.sibling,n.index=e.index,n.ref=e.ref,n}function Ps(e,t,n,o,r,l){var i=2;if(o=e,typeof e=="function")uu(e)&&(i=1);else if(typeof e=="string")i=5;else e:switch(e){case Xr:return xr(n.children,r,l,t);case Id:i=8,r|=8;break;case Dc:return e=Tn(12,n,t,r|2),e.elementType=Dc,e.lanes=l,e;case Bc:return e=Tn(13,n,t,r),e.elementType=Bc,e.lanes=l,e;case zc:return e=Tn(19,n,t,r),e.elementType=zc,e.lanes=l,e;case V0:return ha(n,r,l,t);default:if(typeof e=="object"&&e!==null)switch(e.$$typeof){case X0:i=10;break e;case Q0:i=9;break e;case Nd:i=11;break e;case $d:i=14;break e;case Oo:i=16,o=null;break e}throw Error(H(130,e==null?e:typeof e,""))}return t=Tn(i,n,t,r),t.elementType=e,t.type=o,t.lanes=l,t}function xr(e,t,n,o){return e=Tn(7,e,o,t),e.lanes=n,e}function ha(e,t,n,o){return e=Tn(22,e,o,t),e.elementType=V0,e.lanes=n,e.stateNode={isHidden:!1},e}function Rc(e,t,n){return e=Tn(6,e,null,t),e.lanes=n,e}function Pc(e,t,n){return t=Tn(4,e.children!==null?e.children:[],e.key,t),t.lanes=n,t.stateNode={containerInfo:e.containerInfo,pendingChildren:null,implementation:e.implementation},t}function Xg(e,t,n,o,r){this.tag=t,this.containerInfo=e,this.finishedWork=this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.pendingContext=this.context=null,this.callbackPriority=0,this.eventTimes=mc(0),this.expirationTimes=mc(-1),this.entangledLanes=this.finishedLanes=this.mutableReadLanes=this.expiredLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=mc(0),this.identifierPrefix=o,this.onRecoverableError=r,this.mutableSourceEagerHydrationData=null}function _u(e,t,n,o,r,l,i,s,a){return e=new Xg(e,t,n,s,a),t===1?(t=1,l===!0&&(t|=8)):t=0,l=Tn(3,null,null,t),e.current=l,l.stateNode=e,l.memoizedState={element:o,isDehydrated:n,cache:null,transitions:null,pendingSuspenseBoundaries:null},Kd(l),e}function Qg(e,t,n){var o=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:Yr,key:o==null?null:""+o,children:e,containerInfo:t,implementation:n}}function Wh(e){if(!e)return Jo;e=e._reactInternals;e:{if(Mr(e)!==e||e.tag!==1)throw Error(H(170));var t=e;do{switch(t.tag){case 3:t=t.stateNode.context;break e;case 1:if(pn(t.type)){t=t.stateNode.__reactInternalMemoizedMergedChildContext;break e}}t=t.return}while(t!==null);throw Error(H(171))}if(e.tag===1){var n=e.type;if(pn(n))return Wf(e,n,t)}return t}function Fh(e,t,n,o,r,l,i,s,a){return e=_u(n,o,!0,e,r,l,i,s,a),e.context=Wh(null),n=e.current,o=rn(),r=qo(n),l=So(o,r),l.callback=t??null,Vo(n,l,r),e.current.lanes=r,Mi(e,r,o),mn(e,o),e}function pa(e,t,n,o){var r=t.current,l=rn(),i=qo(r);return n=Wh(n),t.context===null?t.context=n:t.pendingContext=n,t=So(l,i),t.payload={element:e},o=o===void 0?null:o,o!==null&&(t.callback=o),e=Vo(r,t,i),e!==null&&(Gn(e,r,i,l),Es(e,r,i)),i}function oa(e){if(e=e.current,!e.child)return null;switch(e.child.tag){case 5:return e.child.stateNode;default:return e.child.stateNode}}function H0(e,t){if(e=e.memoizedState,e!==null&&e.dehydrated!==null){var n=e.retryLane;e.retryLane=n!==0&&n<t?n:t}}function fu(e,t){H0(e,t),(e=e.alternate)&&H0(e,t)}function Vg(){return null}var jh=typeof reportError=="function"?reportError:function(e){console.error(e)};function hu(e){this._internalRoot=e}ma.prototype.render=hu.prototype.render=function(e){var t=this._internalRoot;if(t===null)throw Error(H(409));pa(e,t,null,null)};ma.prototype.unmount=hu.prototype.unmount=function(){var e=this._internalRoot;if(e!==null){this._internalRoot=null;var t=e.containerInfo;Cr(function(){pa(null,e,null,null)}),t[Eo]=null}};function ma(e){this._internalRoot=e}ma.prototype.unstable_scheduleHydration=function(e){if(e){var t=xf();e={blockedOn:null,target:e,priority:t};for(var n=0;n<Wo.length&&t!==0&&t<Wo[n].priority;n++);Wo.splice(n,0,e),n===0&&wf(e)}};function pu(e){return!(!e||e.nodeType!==1&&e.nodeType!==9&&e.nodeType!==11)}function ga(e){return!(!e||e.nodeType!==1&&e.nodeType!==9&&e.nodeType!==11&&(e.nodeType!==8||e.nodeValue!==" react-mount-point-unstable "))}function U0(){}function Kg(e,t,n,o,r){if(r){if(typeof o=="function"){var l=o;o=function(){var m=oa(i);l.call(m)}}var i=Fh(t,o,e,0,null,!1,!1,"",U0);return e._reactRootContainer=i,e[Eo]=i.current,gi(e.nodeType===8?e.parentNode:e),Cr(),i}for(;r=e.lastChild;)e.removeChild(r);if(typeof o=="function"){var s=o;o=function(){var m=oa(a);s.call(m)}}var a=_u(e,0,!1,null,null,!1,!1,"",U0);return e._reactRootContainer=a,e[Eo]=a.current,gi(e.nodeType===8?e.parentNode:e),Cr(function(){pa(t,a,n,o)}),a}function ya(e,t,n,o,r){var l=n._reactRootContainer;if(l){var i=l;if(typeof r=="function"){var s=r;r=function(){var a=oa(i);s.call(a)}}pa(t,i,e,r)}else i=Kg(n,t,e,r,o);return oa(i)}gf=function(e){switch(e.tag){case 3:var t=e.stateNode;if(t.current.memoizedState.isDehydrated){var n=Zl(t.pendingLanes);n!==0&&(Td(t,n|1),mn(t,Rt()),(Ve&6)===0&&(pl=Rt()+500,nr()))}break;case 13:Cr(function(){var o=Lo(e,1);if(o!==null){var r=rn();Gn(o,e,1,r)}}),fu(e,1)}};Dd=function(e){if(e.tag===13){var t=Lo(e,134217728);if(t!==null){var n=rn();Gn(t,e,134217728,n)}fu(e,134217728)}};yf=function(e){if(e.tag===13){var t=qo(e),n=Lo(e,t);if(n!==null){var o=rn();Gn(n,e,t,o)}fu(e,t)}};xf=function(){return lt};vf=function(e,t){var n=lt;try{return lt=e,t()}finally{lt=n}};Qc=function(e,t,n){switch(t){case"input":if(Wc(e,n),t=n.name,n.type==="radio"&&t!=null){for(n=e;n.parentNode;)n=n.parentNode;for(n=n.querySelectorAll("input[name="+JSON.stringify(""+t)+'][type="radio"]'),t=0;t<n.length;t++){var o=n[t];if(o!==e&&o.form===e.form){var r=aa(o);if(!r)throw Error(H(90));q0(o),Wc(o,r)}}}break;case"textarea":Z0(e,n);break;case"select":t=n.value,t!=null&&ol(e,!!n.multiple,t,!1)}};lf=au;sf=Cr;var qg={usingClientEntryPoint:!1,Events:[Li,qr,aa,of,rf,au]},Vl={findFiberByHostInstance:pr,bundleType:0,version:"18.3.1",rendererPackageName:"react-dom"},Gg={bundleType:Vl.bundleType,version:Vl.version,rendererPackageName:Vl.rendererPackageName,rendererConfig:Vl.rendererConfig,overrideHookState:null,overrideHookStateDeletePath:null,overrideHookStateRenamePath:null,overrideProps:null,overridePropsDeletePath:null,overridePropsRenamePath:null,setErrorHandler:null,setSuspenseHandler:null,scheduleUpdate:null,currentDispatcherRef:No.ReactCurrentDispatcher,findHostInstanceByFiber:function(e){return e=df(e),e===null?null:e.stateNode},findFiberByHostInstance:Vl.findFiberByHostInstance||Vg,findHostInstancesForRefresh:null,scheduleRefresh:null,scheduleRoot:null,setRefreshHandler:null,getCurrentFiber:null,reconcilerVersion:"18.3.1-next-f1338f8080-20240426"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"&&(Kl=__REACT_DEVTOOLS_GLOBAL_HOOK__,!Kl.isDisabled&&Kl.supportsFiber))try{ra=Kl.inject(Gg),_o=Kl}catch{}var Kl;kn.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=qg;kn.createPortal=function(e,t){var n=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!pu(t))throw Error(H(200));return Qg(e,t,null,n)};kn.createRoot=function(e,t){if(!pu(e))throw Error(H(299));var n=!1,o="",r=jh;return t!=null&&(t.unstable_strictMode===!0&&(n=!0),t.identifierPrefix!==void 0&&(o=t.identifierPrefix),t.onRecoverableError!==void 0&&(r=t.onRecoverableError)),t=_u(e,1,!1,null,null,n,!1,o,r),e[Eo]=t.current,gi(e.nodeType===8?e.parentNode:e),new hu(t)};kn.findDOMNode=function(e){if(e==null)return null;if(e.nodeType===1)return e;var t=e._reactInternals;if(t===void 0)throw typeof e.render=="function"?Error(H(188)):(e=Object.keys(e).join(","),Error(H(268,e)));return e=df(t),e=e===null?null:e.stateNode,e};kn.flushSync=function(e){return Cr(e)};kn.hydrate=function(e,t,n){if(!ga(t))throw Error(H(200));return ya(null,e,t,!0,n)};kn.hydrateRoot=function(e,t,n){if(!pu(e))throw Error(H(405));var o=n!=null&&n.hydratedSources||null,r=!1,l="",i=jh;if(n!=null&&(n.unstable_strictMode===!0&&(r=!0),n.identifierPrefix!==void 0&&(l=n.identifierPrefix),n.onRecoverableError!==void 0&&(i=n.onRecoverableError)),t=Fh(t,null,e,1,n??null,r,!1,l,i),e[Eo]=t.current,gi(e),o)for(e=0;e<o.length;e++)n=o[e],r=n._getVersion,r=r(n._source),t.mutableSourceEagerHydrationData==null?t.mutableSourceEagerHydrationData=[n,r]:t.mutableSourceEagerHydrationData.push(n,r);return new ma(t)};kn.render=function(e,t,n){if(!ga(t))throw Error(H(200));return ya(null,e,t,!1,n)};kn.unmountComponentAtNode=function(e){if(!ga(e))throw Error(H(40));return e._reactRootContainer?(Cr(function(){ya(null,null,e,!1,function(){e._reactRootContainer=null,e[Eo]=null})}),!0):!1};kn.unstable_batchedUpdates=au;kn.unstable_renderSubtreeIntoContainer=function(e,t,n,o){if(!ga(n))throw Error(H(200));if(e==null||e._reactInternals===void 0)throw Error(H(38));return ya(e,t,n,!1,o)};kn.version="18.3.1-next-f1338f8080-20240426"});var xa=vo((Wx,Yh)=>{"use strict";function Uh(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(Uh)}catch(e){console.error(e)}}Uh(),Yh.exports=Hh()});var Qh=vo(mu=>{"use strict";var Xh=xa();mu.createRoot=Xh.createRoot,mu.hydrateRoot=Xh.hydrateRoot;var Fx});var Kh=vo(va=>{"use strict";var Zg=Nn(),Jg=Symbol.for("react.element"),ey=Symbol.for("react.fragment"),ty=Object.prototype.hasOwnProperty,ny=Zg.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,oy={key:!0,ref:!0,__self:!0,__source:!0};function Vh(e,t,n){var o,r={},l=null,i=null;n!==void 0&&(l=""+n),t.key!==void 0&&(l=""+t.key),t.ref!==void 0&&(i=t.ref);for(o in t)ty.call(t,o)&&!oy.hasOwnProperty(o)&&(r[o]=t[o]);if(e&&e.defaultProps)for(o in t=e.defaultProps,t)r[o]===void 0&&(r[o]=t[o]);return{$$typeof:Jg,type:e,key:l,ref:i,props:r,_owner:ny.current}}va.Fragment=ey;va.jsx=Vh;va.jsxs=Vh});var sn=vo((Ux,qh)=>{"use strict";qh.exports=Kh()});var Yx=_t(Nn()),Xx=_t(Qh());var nm={};Pm(nm,{Agentation:()=>Mx,AnimatedBunny:()=>My,AnnotationPopupCSS:()=>Di,IconChatEllipsis:()=>wy,IconCheck:()=>cy,IconCheckSmall:()=>dy,IconCheckSmallAnimated:()=>uy,IconCheckmark:()=>by,IconCheckmarkCircle:()=>Cy,IconCheckmarkLarge:()=>ky,IconChevronLeft:()=>zp,IconChevronRight:()=>Sy,IconClose:()=>ay,IconCopyAlt:()=>_y,IconCopyAnimated:()=>Mp,IconEdit:()=>Dp,IconEye:()=>hy,IconEyeAlt:()=>py,IconEyeAnimated:()=>Lp,IconEyeClosed:()=>my,IconEyeMinus:()=>gy,IconGear:()=>Np,IconHelp:()=>Sp,IconLayout:()=>Op,IconListSparkle:()=>Cp,IconMoon:()=>Tp,IconPause:()=>xy,IconPauseAlt:()=>yy,IconPausePlayAnimated:()=>Ip,IconPlayAlt:()=>vy,IconPlus:()=>kp,IconSendAnimated:()=>fy,IconSendArrow:()=>Ep,IconSun:()=>Pp,IconTrash:()=>Bp,IconTrashAlt:()=>$p,IconXmark:()=>Bu,IconXmarkLarge:()=>Rp,PageFeedbackToolbarCSS:()=>Mx,closestCrossingShadow:()=>en,getElementClasses:()=>bl,getElementPath:()=>jp,getNearbyText:()=>wl,getShadowHost:()=>o2,getStorageKey:()=>Bi,identifyAnimationElement:()=>r2,identifyElement:()=>$r,isInShadowDOM:()=>n2,loadAnnotations:()=>Pa,saveAnnotations:()=>zu});var M=_t(Nn(),1),bp=_t(xa(),1),Ct=_t(Nn(),1),E=_t(sn(),1),yt=_t(sn(),1),po=_t(Nn(),1),Wp=_t(xa(),1),Rr=_t(sn(),1),Iu=_t(sn(),1),Ke=_t(Nn(),1),d=_t(sn(),1),dt=_t(sn(),1),St=_t(Nn(),1),c=_t(sn(),1),ke=_t(Nn(),1),He=_t(sn(),1),em=_t(Nn(),1),Cn=_t(sn(),1),Oi=_t(sn(),1),tm=_t(Nn(),1),Cl=_t(sn(),1),Sl=_t(sn(),1),G=_t(sn(),1),F=_t(sn(),1),ry=`.styles-module__popup___IhzrD svg[fill=none] {
  fill: none !important;
}
.styles-module__popup___IhzrD svg[fill=none] :not([fill]) {
  fill: none !important;
}

@keyframes styles-module__popupEnter___AuQDN {
  from {
    opacity: 0;
    transform: translateX(-50%) scale(0.95) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) scale(1) translateY(0);
  }
}
@keyframes styles-module__popupExit___JJKQX {
  from {
    opacity: 1;
    transform: translateX(-50%) scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: translateX(-50%) scale(0.95) translateY(4px);
  }
}
@keyframes styles-module__shake___jdbWe {
  0%, 100% {
    transform: translateX(-50%) scale(1) translateY(0) translateX(0);
  }
  20% {
    transform: translateX(-50%) scale(1) translateY(0) translateX(-3px);
  }
  40% {
    transform: translateX(-50%) scale(1) translateY(0) translateX(3px);
  }
  60% {
    transform: translateX(-50%) scale(1) translateY(0) translateX(-2px);
  }
  80% {
    transform: translateX(-50%) scale(1) translateY(0) translateX(2px);
  }
}
.styles-module__popup___IhzrD {
  position: fixed;
  transform: translateX(-50%);
  width: 280px;
  padding: 0.75rem 1rem 14px;
  background: #1a1a1a;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08);
  z-index: 100001;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  will-change: transform, opacity;
  opacity: 0;
}
.styles-module__popup___IhzrD.styles-module__enter___L7U7N {
  animation: styles-module__popupEnter___AuQDN 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
.styles-module__popup___IhzrD.styles-module__entered___COX-w {
  opacity: 1;
  transform: translateX(-50%) scale(1) translateY(0);
}
.styles-module__popup___IhzrD.styles-module__exit___5eGjE {
  animation: styles-module__popupExit___JJKQX 0.15s ease-in forwards;
}
.styles-module__popup___IhzrD.styles-module__entered___COX-w.styles-module__shake___jdbWe {
  animation: styles-module__shake___jdbWe 0.25s ease-out;
}

.styles-module__header___wWsSi {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5625rem;
}

.styles-module__element___fTV2z {
  font-size: 0.75rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.styles-module__headerToggle___WpW0b {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  flex: 1;
  min-width: 0;
  text-align: left;
}
.styles-module__headerToggle___WpW0b .styles-module__element___fTV2z {
  flex: 1;
}

.styles-module__chevron___ZZJlR {
  color: rgba(255, 255, 255, 0.5);
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  flex-shrink: 0;
}
.styles-module__chevron___ZZJlR.styles-module__expanded___2Hxgv {
  transform: rotate(90deg);
}

.styles-module__stylesWrapper___pnHgy {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.styles-module__stylesWrapper___pnHgy.styles-module__expanded___2Hxgv {
  grid-template-rows: 1fr;
}

.styles-module__stylesInner___YYZe2 {
  overflow: hidden;
}

.styles-module__stylesBlock___VfQKn {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.375rem;
  padding: 0.5rem 0.625rem;
  margin-bottom: 0.5rem;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.6875rem;
  line-height: 1.5;
}

.styles-module__styleLine___1YQiD {
  color: rgba(255, 255, 255, 0.85);
  word-break: break-word;
}

.styles-module__styleProperty___84L1i {
  color: #c792ea;
}

.styles-module__styleValue___q51-h {
  color: rgba(255, 255, 255, 0.85);
}

.styles-module__timestamp___Dtpsv {
  font-size: 0.625rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.35);
  font-variant-numeric: tabular-nums;
  margin-left: 0.5rem;
  flex-shrink: 0;
}

.styles-module__quote___mcMmQ {
  font-size: 12px;
  font-style: italic;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.5rem;
  padding: 0.4rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.25rem;
  line-height: 1.45;
}

.styles-module__textarea___jrSae {
  box-sizing: border-box;
  width: 100%;
  padding: 0.5rem 0.625rem;
  font-size: 0.8125rem;
  font-family: inherit;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  resize: none;
  outline: none;
  transition: border-color 0.15s ease;
}
.styles-module__textarea___jrSae:focus {
  border-color: var(--agentation-color-blue);
}
.styles-module__textarea___jrSae.styles-module__green___99l3h:focus {
  border-color: var(--agentation-color-green);
}
.styles-module__textarea___jrSae::placeholder {
  color: rgba(255, 255, 255, 0.35);
}
.styles-module__textarea___jrSae::-webkit-scrollbar {
  width: 6px;
}
.styles-module__textarea___jrSae::-webkit-scrollbar-track {
  background: transparent;
}
.styles-module__textarea___jrSae::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.styles-module__actions___D6x3f {
  display: flex;
  justify-content: flex-end;
  gap: 0.375rem;
  margin-top: 0.5rem;
}

.styles-module__cancel___hRjnL,
.styles-module__submit___K-mIR {
  padding: 0.4rem 0.875rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 1rem;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, opacity 0.15s ease;
}

.styles-module__cancel___hRjnL {
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
}
.styles-module__cancel___hRjnL:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.styles-module__submit___K-mIR {
  color: white;
}
.styles-module__submit___K-mIR:hover:not(:disabled) {
  filter: brightness(0.9);
}
.styles-module__submit___K-mIR:disabled {
  cursor: not-allowed;
}

.styles-module__deleteWrapper___oSjdo {
  margin-right: auto;
}

.styles-module__deleteButton___4VuAE {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease;
}
.styles-module__deleteButton___4VuAE:hover {
  background-color: color-mix(in srgb, var(--agentation-color-red) 25%, transparent);
  color: var(--agentation-color-red);
}
.styles-module__deleteButton___4VuAE:active {
  transform: scale(0.92);
}

.styles-module__light___6AaSQ.styles-module__popup___IhzrD {
  background: #fff;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.06);
}
.styles-module__light___6AaSQ .styles-module__element___fTV2z {
  color: rgba(0, 0, 0, 0.6);
}
.styles-module__light___6AaSQ .styles-module__timestamp___Dtpsv {
  color: rgba(0, 0, 0, 0.4);
}
.styles-module__light___6AaSQ .styles-module__chevron___ZZJlR {
  color: rgba(0, 0, 0, 0.4);
}
.styles-module__light___6AaSQ .styles-module__stylesBlock___VfQKn {
  background: rgba(0, 0, 0, 0.03);
}
.styles-module__light___6AaSQ .styles-module__styleLine___1YQiD {
  color: rgba(0, 0, 0, 0.75);
}
.styles-module__light___6AaSQ .styles-module__styleProperty___84L1i {
  color: #7c3aed;
}
.styles-module__light___6AaSQ .styles-module__styleValue___q51-h {
  color: rgba(0, 0, 0, 0.75);
}
.styles-module__light___6AaSQ .styles-module__quote___mcMmQ {
  color: rgba(0, 0, 0, 0.55);
  background: rgba(0, 0, 0, 0.04);
}
.styles-module__light___6AaSQ .styles-module__textarea___jrSae {
  background: rgba(0, 0, 0, 0.03);
  color: #1a1a1a;
  border-color: rgba(0, 0, 0, 0.12);
}
.styles-module__light___6AaSQ .styles-module__textarea___jrSae::placeholder {
  color: rgba(0, 0, 0, 0.4);
}
.styles-module__light___6AaSQ .styles-module__textarea___jrSae::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
}
.styles-module__light___6AaSQ .styles-module__cancel___hRjnL {
  color: rgba(0, 0, 0, 0.5);
}
.styles-module__light___6AaSQ .styles-module__cancel___hRjnL:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.75);
}
.styles-module__light___6AaSQ .styles-module__deleteButton___4VuAE {
  color: rgba(0, 0, 0, 0.4);
}
.styles-module__light___6AaSQ .styles-module__deleteButton___4VuAE:hover {
  background-color: color-mix(in srgb, var(--agentation-color-red) 25%, transparent);
  color: var(--agentation-color-red);
}`,ly={popup:"styles-module__popup___IhzrD",enter:"styles-module__enter___L7U7N",popupEnter:"styles-module__popupEnter___AuQDN",entered:"styles-module__entered___COX-w",exit:"styles-module__exit___5eGjE",popupExit:"styles-module__popupExit___JJKQX",shake:"styles-module__shake___jdbWe",header:"styles-module__header___wWsSi",element:"styles-module__element___fTV2z",headerToggle:"styles-module__headerToggle___WpW0b",chevron:"styles-module__chevron___ZZJlR",expanded:"styles-module__expanded___2Hxgv",stylesWrapper:"styles-module__stylesWrapper___pnHgy",stylesInner:"styles-module__stylesInner___YYZe2",stylesBlock:"styles-module__stylesBlock___VfQKn",styleLine:"styles-module__styleLine___1YQiD",styleProperty:"styles-module__styleProperty___84L1i",styleValue:"styles-module__styleValue___q51-h",timestamp:"styles-module__timestamp___Dtpsv",quote:"styles-module__quote___mcMmQ",textarea:"styles-module__textarea___jrSae",green:"styles-module__green___99l3h",actions:"styles-module__actions___D6x3f",cancel:"styles-module__cancel___hRjnL",submit:"styles-module__submit___K-mIR",deleteWrapper:"styles-module__deleteWrapper___oSjdo",deleteButton:"styles-module__deleteButton___4VuAE",light:"styles-module__light___6AaSQ"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-annotation-popup-css-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-annotation-popup-css-styles",document.head.appendChild(e)),e.textContent=ry}var ct=ly,iy=`.icon-transitions-module__iconState___uqK9J {
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform-origin: center;
}

.icon-transitions-module__iconStateFast___HxlMm {
  transition: opacity 0.15s ease, transform 0.15s ease;
  transform-origin: center;
}

.icon-transitions-module__iconFade___nPwXg {
  transition: opacity 0.2s ease;
}

.icon-transitions-module__iconFadeFast___Ofb2t {
  transition: opacity 0.15s ease;
}

.icon-transitions-module__visible___PlHsU {
  opacity: 1 !important;
}

.icon-transitions-module__visibleScaled___8Qog- {
  opacity: 1 !important;
  transform: scale(1);
}

.icon-transitions-module__hidden___ETykt {
  opacity: 0 !important;
}

.icon-transitions-module__hiddenScaled___JXn-m {
  opacity: 0 !important;
  transform: scale(0.8);
}

.icon-transitions-module__sending___uaLN- {
  opacity: 0.5 !important;
  transform: scale(0.8);
}`,sy={iconState:"icon-transitions-module__iconState___uqK9J",iconStateFast:"icon-transitions-module__iconStateFast___HxlMm",iconFade:"icon-transitions-module__iconFade___nPwXg",iconFadeFast:"icon-transitions-module__iconFadeFast___Ofb2t",visible:"icon-transitions-module__visible___PlHsU",visibleScaled:"icon-transitions-module__visibleScaled___8Qog-",hidden:"icon-transitions-module__hidden___ETykt",hiddenScaled:"icon-transitions-module__hiddenScaled___JXn-m",sending:"icon-transitions-module__sending___uaLN-"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-components-icon-transitions");e||(e=document.createElement("style"),e.id="feedback-tool-styles-components-icon-transitions",document.head.appendChild(e)),e.textContent=iy}var Ue=sy,ay=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",children:(0,E.jsx)("path",{d:"M4 4l8 8M12 4l-8 8",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})}),kp=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",children:(0,E.jsx)("path",{d:"M8 3v10M3 8h10",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})}),cy=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",children:(0,E.jsx)("path",{d:"M3 8l3.5 3.5L13 5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),dy=({size:e=14})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 14 14",fill:"none",children:(0,E.jsx)("path",{d:"M3.9375 7L6.125 9.1875L10.5 4.8125",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),Cp=({size:e=24,style:t={}})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",style:t,children:[(0,E.jsxs)("g",{clipPath:"url(#clip0_list_sparkle)",children:[(0,E.jsx)("path",{d:"M11.5 12L5.5 12",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M18.5 6.75L5.5 6.75",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M9.25 17.25L5.5 17.25",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M16 12.75L16.5179 13.9677C16.8078 14.6494 17.3506 15.1922 18.0323 15.4821L19.25 16L18.0323 16.5179C17.3506 16.8078 16.8078 17.3506 16.5179 18.0323L16 19.25L15.4821 18.0323C15.1922 17.3506 14.6494 16.8078 13.9677 16.5179L12.75 16L13.9677 15.4821C14.6494 15.1922 15.1922 14.6494 15.4821 13.9677L16 12.75Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinejoin:"round"})]}),(0,E.jsx)("defs",{children:(0,E.jsx)("clipPath",{id:"clip0_list_sparkle",children:(0,E.jsx)("rect",{width:"24",height:"24",fill:"white"})})})]}),Sp=({size:e=20,...t})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 20 20",fill:"none",xmlns:"http://www.w3.org/2000/svg",...t,children:[(0,E.jsx)("circle",{cx:"10",cy:"10",r:"5.375",stroke:"currentColor",strokeWidth:"1.25"}),(0,E.jsx)("path",{d:"M8.5 8.5C8.73 7.85 9.31 7.49 10 7.5C10.86 7.51 11.5 8.13 11.5 9C11.5 10.08 10 10.5 10 10.5V10.75",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("circle",{cx:"10",cy:"12.625",r:"0.625",fill:"currentColor"})]}),uy=({size:e=14})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 14 14",fill:"none",children:[(0,E.jsx)("style",{children:`
      @keyframes checkDraw {
        0% {
          stroke-dashoffset: 12;
        }
        100% {
          stroke-dashoffset: 0;
        }
      }
      @keyframes checkBounce {
        0% {
          transform: scale(0.5);
          opacity: 0;
        }
        50% {
          transform: scale(1.12);
          opacity: 1;
        }
        75% {
          transform: scale(0.95);
        }
        100% {
          transform: scale(1);
        }
      }
      .check-path-animated {
        stroke-dasharray: 12;
        stroke-dashoffset: 0;
        transform-origin: center;
        animation: checkDraw 0.18s ease-out, checkBounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      }
    `}),(0,E.jsx)("path",{className:"check-path-animated",d:"M3.9375 7L6.125 9.1875L10.5 4.8125",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),_y=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M4.75 11.25C4.75 10.4216 5.42157 9.75 6.25 9.75H12.75C13.5784 9.75 14.25 10.4216 14.25 11.25V17.75C14.25 18.5784 13.5784 19.25 12.75 19.25H6.25C5.42157 19.25 4.75 18.5784 4.75 17.75V11.25Z",stroke:"currentColor",strokeWidth:"1.5"}),(0,E.jsx)("path",{d:"M17.25 14.25H17.75C18.5784 14.25 19.25 13.5784 19.25 12.75V6.25C19.25 5.42157 18.5784 4.75 17.75 4.75H11.25C10.4216 4.75 9.75 5.42157 9.75 6.25V6.75",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),Mp=({size:e=24,copied:t=!1,tint:n})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",style:n?{color:n,transition:"color 0.3s ease"}:void 0,children:[(0,E.jsxs)("g",{className:`${Ue.iconState} ${t?Ue.hiddenScaled:Ue.visibleScaled}`,children:[(0,E.jsx)("path",{d:"M4.75 11.25C4.75 10.4216 5.42157 9.75 6.25 9.75H12.75C13.5784 9.75 14.25 10.4216 14.25 11.25V17.75C14.25 18.5784 13.5784 19.25 12.75 19.25H6.25C5.42157 19.25 4.75 18.5784 4.75 17.75V11.25Z",stroke:"currentColor",strokeWidth:"1.5"}),(0,E.jsx)("path",{d:"M17.25 14.25H17.75C18.5784 14.25 19.25 13.5784 19.25 12.75V6.25C19.25 5.42157 18.5784 4.75 17.75 4.75H11.25C10.4216 4.75 9.75 5.42157 9.75 6.25V6.75",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),(0,E.jsxs)("g",{className:`${Ue.iconState} ${t?Ue.visibleScaled:Ue.hiddenScaled}`,children:[(0,E.jsx)("path",{d:"M12 20C7.58172 20 4 16.4182 4 12C4 7.58172 7.58172 4 12 4C16.4182 4 20 7.58172 20 12C20 16.4182 16.4182 20 12 20Z",stroke:"var(--agentation-color-green)",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M15 10L11 14.25L9.25 12.25",stroke:"var(--agentation-color-green)",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]})]}),Ep=({size:e=24,state:t="idle"})=>{let n=t==="idle",o=t==="sent",r=t==="failed",l=t==="sending";return(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("g",{className:`${Ue.iconStateFast} ${n?Ue.visibleScaled:l?Ue.sending:Ue.hiddenScaled}`,children:(0,E.jsx)("path",{d:"M9.875 14.125L12.3506 19.6951C12.7184 20.5227 13.9091 20.4741 14.2083 19.6193L18.8139 6.46032C19.0907 5.6695 18.3305 4.90933 17.5397 5.18611L4.38072 9.79174C3.52589 10.0909 3.47731 11.2816 4.30494 11.6494L9.875 14.125ZM9.875 14.125L13.375 10.625",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),(0,E.jsxs)("g",{className:`${Ue.iconStateFast} ${o?Ue.visibleScaled:Ue.hiddenScaled}`,children:[(0,E.jsx)("path",{d:"M12 20C7.58172 20 4 16.4182 4 12C4 7.58172 7.58172 4 12 4C16.4182 4 20 7.58172 20 12C20 16.4182 16.4182 20 12 20Z",stroke:"var(--agentation-color-green)",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M15 10L11 14.25L9.25 12.25",stroke:"var(--agentation-color-green)",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),(0,E.jsxs)("g",{className:`${Ue.iconStateFast} ${r?Ue.visibleScaled:Ue.hiddenScaled}`,children:[(0,E.jsx)("path",{d:"M12 20C7.58172 20 4 16.4182 4 12C4 7.58172 7.58172 4 12 4C16.4182 4 20 7.58172 20 12C20 16.4182 16.4182 20 12 20Z",stroke:"var(--agentation-color-red)",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M12 8V12",stroke:"var(--agentation-color-red)",strokeWidth:"1.5",strokeLinecap:"round"}),(0,E.jsx)("circle",{cx:"12",cy:"15",r:"0.5",fill:"var(--agentation-color-red)",stroke:"var(--agentation-color-red)",strokeWidth:"1"})]})]})},fy=({size:e=24,sent:t=!1})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 22 21",fill:"none",children:[(0,E.jsxs)("g",{className:`${Ue.iconState} ${t?Ue.hiddenScaled:Ue.visibleScaled}`,children:[(0,E.jsx)("path",{d:"M9.5 5H6.5C4.84315 5 3.5 6.34315 3.5 8V15C3.5 16.6569 4.84315 18 6.5 18H13.5C15.1569 18 16.5 16.6569 16.5 15V12",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"}),(0,E.jsx)("path",{d:"M13.5 8.5L18.5 3.5M18.5 3.5L14.4524 3.5M18.5 3.5L18.5 7.54762",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M7.5 13.75H12.5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"}),(0,E.jsx)("path",{d:"M7.5 10.75H10.5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),(0,E.jsxs)("g",{className:`${Ue.iconState} ${t?Ue.visibleScaled:Ue.hiddenScaled}`,children:[(0,E.jsx)("path",{d:"M11 19C6.58172 19 3 15.4182 3 11C3 6.58172 6.58172 3 11 3C15.4182 3 19 6.58172 19 11C19 15.4182 15.4182 19 11 19Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M14 9L10 13.25L8.25 11.25",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]})]}),hy=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M4.91516 12.7108C4.63794 12.2883 4.63705 11.7565 4.91242 11.3328C5.84146 9.9033 8.30909 6.74994 12 6.74994C15.6909 6.74994 18.1585 9.9033 19.0876 11.3328C19.3629 11.7565 19.3621 12.2883 19.0848 12.7108C18.1537 14.13 15.6873 17.2499 12 17.2499C8.31272 17.2499 5.8463 14.13 4.91516 12.7108Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M12 14.25C13.2426 14.25 14.25 13.2426 14.25 12C14.25 10.7574 13.2426 9.75 12 9.75C10.7574 9.75 9.75 10.7574 9.75 12C9.75 13.2426 10.7574 14.25 12 14.25Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),py=({size:e=24})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M3.91752 12.7539C3.65127 12.2996 3.65037 11.7515 3.9149 11.2962C4.9042 9.59346 7.72688 5.49994 12 5.49994C16.2731 5.49994 19.0958 9.59346 20.0851 11.2962C20.3496 11.7515 20.3487 12.2996 20.0825 12.7539C19.0908 14.4459 16.2694 18.4999 12 18.4999C7.73064 18.4999 4.90918 14.4459 3.91752 12.7539Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M12 14.8261C13.5608 14.8261 14.8261 13.5608 14.8261 12C14.8261 10.4392 13.5608 9.17392 12 9.17392C10.4392 9.17392 9.17391 10.4392 9.17391 12C9.17391 13.5608 10.4392 14.8261 12 14.8261Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),my=({size:e=24})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M18.6025 9.28503C18.9174 8.9701 19.4364 8.99481 19.7015 9.35271C20.1484 9.95606 20.4943 10.507 20.7342 10.9199C21.134 11.6086 21.1329 12.4454 20.7303 13.1328C20.2144 14.013 19.2151 15.5225 17.7723 16.8193C16.3293 18.1162 14.3852 19.2497 12.0008 19.25C11.4192 19.25 10.8638 19.1823 10.3355 19.0613C9.77966 18.934 9.63498 18.2525 10.0382 17.8493C10.2412 17.6463 10.5374 17.573 10.8188 17.6302C11.1993 17.7076 11.5935 17.75 12.0008 17.75C13.8848 17.7497 15.4867 16.8568 16.7693 15.7041C18.0522 14.5511 18.9606 13.1867 19.4363 12.375C19.5656 12.1543 19.5659 11.8943 19.4373 11.6729C19.2235 11.3049 18.921 10.8242 18.5364 10.3003C18.3085 9.98991 18.3302 9.5573 18.6025 9.28503ZM12.0008 4.75C12.5814 4.75006 13.1358 4.81803 13.6632 4.93953C14.2182 5.06741 14.362 5.74812 13.9593 6.15091C13.7558 6.35435 13.4589 6.42748 13.1771 6.36984C12.7983 6.29239 12.4061 6.25006 12.0008 6.25C10.1167 6.25 8.51415 7.15145 7.23028 8.31543C5.94678 9.47919 5.03918 10.8555 4.56426 11.6729C4.43551 11.8945 4.43582 12.1542 4.56524 12.375C4.77587 12.7343 5.07189 13.2012 5.44718 13.7105C5.67623 14.0213 5.65493 14.4552 5.38193 14.7282C5.0671 15.0431 4.54833 15.0189 4.28292 14.6614C3.84652 14.0736 3.50813 13.5369 3.27129 13.1328C2.86831 12.4451 2.86717 11.6088 3.26739 10.9199C3.78185 10.0345 4.77959 8.51239 6.22247 7.2041C7.66547 5.89584 9.61202 4.75 12.0008 4.75Z",fill:"currentColor"}),(0,E.jsx)("path",{d:"M5 19L19 5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),Lp=({size:e=24,isOpen:t=!0})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsxs)("g",{className:`${Ue.iconFade} ${t?Ue.visible:Ue.hidden}`,children:[(0,E.jsx)("path",{d:"M3.91752 12.7539C3.65127 12.2996 3.65037 11.7515 3.9149 11.2962C4.9042 9.59346 7.72688 5.49994 12 5.49994C16.2731 5.49994 19.0958 9.59346 20.0851 11.2962C20.3496 11.7515 20.3487 12.2996 20.0825 12.7539C19.0908 14.4459 16.2694 18.4999 12 18.4999C7.73064 18.4999 4.90918 14.4459 3.91752 12.7539Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M12 14.8261C13.5608 14.8261 14.8261 13.5608 14.8261 12C14.8261 10.4392 13.5608 9.17392 12 9.17392C10.4392 9.17392 9.17391 10.4392 9.17391 12C9.17391 13.5608 10.4392 14.8261 12 14.8261Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),(0,E.jsxs)("g",{className:`${Ue.iconFade} ${t?Ue.hidden:Ue.visible}`,children:[(0,E.jsx)("path",{d:"M18.6025 9.28503C18.9174 8.9701 19.4364 8.99481 19.7015 9.35271C20.1484 9.95606 20.4943 10.507 20.7342 10.9199C21.134 11.6086 21.1329 12.4454 20.7303 13.1328C20.2144 14.013 19.2151 15.5225 17.7723 16.8193C16.3293 18.1162 14.3852 19.2497 12.0008 19.25C11.4192 19.25 10.8638 19.1823 10.3355 19.0613C9.77966 18.934 9.63498 18.2525 10.0382 17.8493C10.2412 17.6463 10.5374 17.573 10.8188 17.6302C11.1993 17.7076 11.5935 17.75 12.0008 17.75C13.8848 17.7497 15.4867 16.8568 16.7693 15.7041C18.0522 14.5511 18.9606 13.1867 19.4363 12.375C19.5656 12.1543 19.5659 11.8943 19.4373 11.6729C19.2235 11.3049 18.921 10.8242 18.5364 10.3003C18.3085 9.98991 18.3302 9.5573 18.6025 9.28503ZM12.0008 4.75C12.5814 4.75006 13.1358 4.81803 13.6632 4.93953C14.2182 5.06741 14.362 5.74812 13.9593 6.15091C13.7558 6.35435 13.4589 6.42748 13.1771 6.36984C12.7983 6.29239 12.4061 6.25006 12.0008 6.25C10.1167 6.25 8.51415 7.15145 7.23028 8.31543C5.94678 9.47919 5.03918 10.8555 4.56426 11.6729C4.43551 11.8945 4.43582 12.1542 4.56524 12.375C4.77587 12.7343 5.07189 13.2012 5.44718 13.7105C5.67623 14.0213 5.65493 14.4552 5.38193 14.7282C5.0671 15.0431 4.54833 15.0189 4.28292 14.6614C3.84652 14.0736 3.50813 13.5369 3.27129 13.1328C2.86831 12.4451 2.86717 11.6088 3.26739 10.9199C3.78185 10.0345 4.77959 8.51239 6.22247 7.2041C7.66547 5.89584 9.61202 4.75 12.0008 4.75Z",fill:"currentColor"}),(0,E.jsx)("path",{d:"M5 19L19 5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]})]}),Ip=({size:e=24,isPaused:t=!1})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsxs)("g",{className:`${Ue.iconFadeFast} ${t?Ue.hidden:Ue.visible}`,children:[(0,E.jsx)("path",{d:"M8 6L8 18",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"}),(0,E.jsx)("path",{d:"M16 18L16 6",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),(0,E.jsx)("path",{className:`${Ue.iconFadeFast} ${t?Ue.visible:Ue.hidden}`,d:"M17.75 10.701C18.75 11.2783 18.75 12.7217 17.75 13.299L8.75 18.4952C7.75 19.0725 6.5 18.3509 6.5 17.1962L6.5 6.80384C6.5 5.64914 7.75 4.92746 8.75 5.50481L17.75 10.701Z",stroke:"currentColor",strokeWidth:"1.5"})]}),gy=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M4.91516 12.7108C4.63794 12.2883 4.63705 11.7565 4.91242 11.3328C5.84146 9.9033 8.30909 6.74994 12 6.74994C15.6909 6.74994 18.1585 9.9033 19.0876 11.3328C19.3629 11.7565 19.3621 12.2883 19.0848 12.7108C18.1537 14.13 15.6873 17.2499 12 17.2499C8.31272 17.2499 5.8463 14.13 4.91516 12.7108Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M9 12H15",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),Np=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M10.6504 5.81117C10.9939 4.39628 13.0061 4.39628 13.3496 5.81117C13.5715 6.72517 14.6187 7.15891 15.4219 6.66952C16.6652 5.91193 18.0881 7.33479 17.3305 8.57815C16.8411 9.38134 17.2748 10.4285 18.1888 10.6504C19.6037 10.9939 19.6037 13.0061 18.1888 13.3496C17.2748 13.5715 16.8411 14.6187 17.3305 15.4219C18.0881 16.6652 16.6652 18.0881 15.4219 17.3305C14.6187 16.8411 13.5715 17.2748 13.3496 18.1888C13.0061 19.6037 10.9939 19.6037 10.6504 18.1888C10.4285 17.2748 9.38135 16.8411 8.57815 17.3305C7.33479 18.0881 5.91193 16.6652 6.66952 15.4219C7.15891 14.6187 6.72517 13.5715 5.81117 13.3496C4.39628 13.0061 4.39628 10.9939 5.81117 10.6504C6.72517 10.4285 7.15891 9.38134 6.66952 8.57815C5.91193 7.33479 7.33479 5.91192 8.57815 6.66952C9.38135 7.15891 10.4285 6.72517 10.6504 5.81117Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("circle",{cx:"12",cy:"12",r:"2.5",stroke:"currentColor",strokeWidth:"1.5"})]}),yy=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M9.25 5.75C9.80228 5.75 10.25 6.19772 10.25 6.75L10.25 17.25C10.25 17.8023 9.80228 18.25 9.25 18.25L6.75 18.25C6.19772 18.25 5.75 17.8023 5.75 17.25L5.75 6.75C5.75 6.19772 6.19772 5.75 6.75 5.75L9.25 5.75Z",stroke:"currentColor",strokeWidth:"1.5"}),(0,E.jsx)("path",{d:"M17.25 5.75C17.8023 5.75 18.25 6.19772 18.25 6.75L18.25 17.25C18.25 17.8023 17.8023 18.25 17.25 18.25L14.75 18.25C14.1977 18.25 13.75 17.8023 13.75 17.25L13.75 6.75C13.75 6.19772 14.1977 5.75 14.75 5.75L17.25 5.75Z",stroke:"currentColor",strokeWidth:"1.5"})]}),xy=({size:e=24})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("path",{d:"M8 6L8 18",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"}),(0,E.jsx)("path",{d:"M16 18L16 6",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round"})]}),vy=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:(0,E.jsx)("path",{d:"M17.75 10.701C18.75 11.2783 18.75 12.7217 17.75 13.299L8.75 18.4952C7.75 19.0725 6.5 18.3509 6.5 17.1962L6.5 6.80384C6.5 5.64914 7.75 4.92746 8.75 5.50481L17.75 10.701Z",stroke:"currentColor",strokeWidth:"1.5"})}),$p=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:(0,E.jsx)("path",{d:"M13.5 4C14.7426 4 15.75 5.00736 15.75 6.25V7H18.5C18.9142 7 19.25 7.33579 19.25 7.75C19.25 8.16421 18.9142 8.5 18.5 8.5H17.9678L17.6328 16.2217C17.61 16.7475 17.5912 17.1861 17.5469 17.543C17.5015 17.9087 17.4225 18.2506 17.2461 18.5723C16.9747 19.0671 16.5579 19.4671 16.0518 19.7168C15.7227 19.8791 15.3772 19.9422 15.0098 19.9717C14.6514 20.0004 14.2126 20 13.6865 20H10.3135C9.78735 20 9.34856 20.0004 8.99023 19.9717C8.62278 19.9422 8.27729 19.8791 7.94824 19.7168C7.44205 19.4671 7.02532 19.0671 6.75391 18.5723C6.57751 18.2506 6.49853 17.9087 6.45312 17.543C6.40883 17.1861 6.39005 16.7475 6.36719 16.2217L6.03223 8.5H5.5C5.08579 8.5 4.75 8.16421 4.75 7.75C4.75 7.33579 5.08579 7 5.5 7H8.25V6.25C8.25 5.00736 9.25736 4 10.5 4H13.5ZM7.86621 16.1562C7.89013 16.7063 7.90624 17.0751 7.94141 17.3584C7.97545 17.6326 8.02151 17.7644 8.06934 17.8516C8.19271 18.0763 8.38239 18.2577 8.6123 18.3711C8.70153 18.4151 8.83504 18.4545 9.11035 18.4766C9.39482 18.4994 9.76335 18.5 10.3135 18.5H13.6865C14.2367 18.5 14.6052 18.4994 14.8896 18.4766C15.165 18.4545 15.2985 18.4151 15.3877 18.3711C15.6176 18.2577 15.8073 18.0763 15.9307 17.8516C15.9785 17.7644 16.0245 17.6326 16.0586 17.3584C16.0938 17.0751 16.1099 16.7063 16.1338 16.1562L16.4668 8.5H7.5332L7.86621 16.1562ZM9.97656 10.75C10.3906 10.7371 10.7371 11.0626 10.75 11.4766L10.875 15.4766C10.8879 15.8906 10.5624 16.2371 10.1484 16.25C9.73443 16.2629 9.38794 15.9374 9.375 15.5234L9.25 11.5234C9.23706 11.1094 9.56255 10.7629 9.97656 10.75ZM14.0244 10.75C14.4384 10.7635 14.7635 11.1105 14.75 11.5244L14.6201 15.5244C14.6066 15.9384 14.2596 16.2634 13.8457 16.25C13.4317 16.2365 13.1067 15.8896 13.1201 15.4756L13.251 11.4756C13.2645 11.0617 13.6105 10.7366 14.0244 10.75ZM10.5 5.5C10.0858 5.5 9.75 5.83579 9.75 6.25V7H14.25V6.25C14.25 5.83579 13.9142 5.5 13.5 5.5H10.5Z",fill:"currentColor"})}),wy=({size:e=16,style:t={}})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",style:t,children:[(0,E.jsx)("path",{d:"M18.8875 19.25L19.6112 19.0533C19.6823 19.3148 19.6068 19.5943 19.4137 19.7844C19.2206 19.9746 18.9399 20.0457 18.6795 19.9706L18.8875 19.25ZM14.9631 18.244L15.263 18.9314L14.9631 18.244ZM18.0914 15.6309L17.4669 15.2156L18.0914 15.6309ZM4.75 11.8041H5.5C5.5 15.2664 8.39065 18.1081 12 18.1081V18.8581V19.6081C7.60123 19.6081 4 16.1334 4 11.8041H4.75ZM19.25 11.8041H18.5C18.5 8.34166 15.6094 5.5 12 5.5V4.75V4C16.3988 4 20 7.47476 20 11.8041H19.25ZM12 4.75V5.5C8.39065 5.5 5.5 8.34166 5.5 11.8041H4.75H4C4 7.47476 7.60123 4 12 4V4.75ZM18.0914 15.6309L17.4669 15.2156C18.1213 14.2315 18.5 13.0612 18.5 11.8041H19.25H20C20 13.3681 19.5276 14.8257 18.716 16.0462L18.0914 15.6309ZM18.8875 19.25L18.1638 19.4467L17.2953 16.2517L18.019 16.055L18.7428 15.8583L19.6112 19.0533L18.8875 19.25ZM12 18.8581V18.1081C12.9509 18.1081 13.8518 17.9105 14.6632 17.5565L14.9631 18.244L15.263 18.9314C14.2652 19.3667 13.1603 19.6081 12 19.6081V18.8581ZM15.3144 18.2188L15.5224 17.4982L19.0955 18.5294L18.8875 19.25L18.6795 19.9706L15.1064 18.9394L15.3144 18.2188ZM14.9631 18.244L14.6632 17.5565C14.925 17.4423 15.2286 17.4134 15.5224 17.4982L15.3144 18.2188L15.1064 18.9394C15.1677 18.957 15.223 18.9489 15.263 18.9314L14.9631 18.244ZM18.0914 15.6309L18.716 16.0462C18.7451 16.0024 18.7636 15.9351 18.7428 15.8583L18.019 16.055L17.2953 16.2517C17.1957 15.8853 17.2716 15.5093 17.4669 15.2156L18.0914 15.6309Z",fill:"currentColor"}),(0,E.jsx)("circle",{cx:"15",cy:"11.75",r:"1",fill:"currentColor"}),(0,E.jsx)("circle",{cx:"12",cy:"11.75",r:"1",fill:"currentColor"}),(0,E.jsx)("circle",{cx:"9",cy:"11.75",r:"1",fill:"currentColor"})]}),by=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("g",{clipPath:"url(#clip0_2_45)",children:(0,E.jsx)("path",{d:"M16.25 8.75L10 15.25L7.25 12.25",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),(0,E.jsx)("defs",{children:(0,E.jsx)("clipPath",{id:"clip0_2_45",children:(0,E.jsx)("rect",{width:"24",height:"24",fill:"white"})})})]}),ky=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("g",{clipPath:"url(#clip0_2_37)",children:(0,E.jsx)("path",{d:"M17.5962 7.75L9.42308 16.25L6.15385 12.6538",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),(0,E.jsx)("defs",{children:(0,E.jsx)("clipPath",{id:"clip0_2_37",children:(0,E.jsx)("rect",{width:"24",height:"24",fill:"white"})})})]}),Cy=({size:e=24})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsxs)("g",{clipPath:"url(#clip0_checkmark_circle)",children:[(0,E.jsx)("path",{d:"M12 20C7.58172 20 4 16.4182 4 12C4 7.58172 7.58172 4 12 4C16.4182 4 20 7.58172 20 12C20 16.4182 16.4182 20 12 20Z",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M15 10L11 14.25L9.25 12.25",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),(0,E.jsx)("defs",{children:(0,E.jsx)("clipPath",{id:"clip0_checkmark_circle",children:(0,E.jsx)("rect",{width:"24",height:"24",fill:"white"})})})]}),Bu=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsxs)("g",{clipPath:"url(#clip0_2_53)",children:[(0,E.jsx)("path",{d:"M16.25 16.25L7.75 7.75",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M7.75 16.25L16.25 7.75",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})]}),(0,E.jsx)("defs",{children:(0,E.jsx)("clipPath",{id:"clip0_2_53",children:(0,E.jsx)("rect",{width:"24",height:"24",fill:"white"})})})]}),Rp=({size:e=24})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:(0,E.jsx)("path",{d:"M16.7198 6.21973C17.0127 5.92683 17.4874 5.92683 17.7803 6.21973C18.0732 6.51262 18.0732 6.9874 17.7803 7.28027L13.0606 12L17.7803 16.7197C18.0732 17.0126 18.0732 17.4874 17.7803 17.7803C17.4875 18.0731 17.0127 18.0731 16.7198 17.7803L12.0001 13.0605L7.28033 17.7803C6.98746 18.0731 6.51268 18.0731 6.21979 17.7803C5.92689 17.4874 5.92689 17.0126 6.21979 16.7197L10.9395 12L6.21979 7.28027C5.92689 6.98738 5.92689 6.51262 6.21979 6.21973C6.51268 5.92683 6.98744 5.92683 7.28033 6.21973L12.0001 10.9395L16.7198 6.21973Z",fill:"currentColor"})}),Pp=({size:e=16})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 20 20",fill:"none",children:[(0,E.jsx)("path",{d:"M9.99999 12.7082C11.4958 12.7082 12.7083 11.4956 12.7083 9.99984C12.7083 8.50407 11.4958 7.2915 9.99999 7.2915C8.50422 7.2915 7.29166 8.50407 7.29166 9.99984C7.29166 11.4956 8.50422 12.7082 9.99999 12.7082Z",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M10 3.9585V5.05698",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M10 14.9429V16.0414",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M5.7269 5.72656L6.50682 6.50649",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M13.4932 13.4932L14.2731 14.2731",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M3.95834 10H5.05683",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M14.9432 10H16.0417",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M5.7269 14.2731L6.50682 13.4932",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"}),(0,E.jsx)("path",{d:"M13.4932 6.50649L14.2731 5.72656",stroke:"currentColor",strokeWidth:"1.25",strokeLinecap:"round",strokeLinejoin:"round"})]}),Tp=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 20 20",fill:"none",children:(0,E.jsx)("path",{d:"M15.5 10.4955C15.4037 11.5379 15.0124 12.5314 14.3721 13.3596C13.7317 14.1878 12.8688 14.8165 11.8841 15.1722C10.8995 15.5278 9.83397 15.5957 8.81217 15.3679C7.79038 15.1401 6.8546 14.6259 6.11434 13.8857C5.37408 13.1454 4.85995 12.2096 4.63211 11.1878C4.40427 10.166 4.47215 9.10048 4.82781 8.11585C5.18346 7.13123 5.81218 6.26825 6.64039 5.62791C7.4686 4.98756 8.46206 4.59634 9.5045 4.5C8.89418 5.32569 8.60049 6.34302 8.67685 7.36695C8.75321 8.39087 9.19454 9.35339 9.92058 10.0794C10.6466 10.8055 11.6091 11.2468 12.6331 11.3231C13.657 11.3995 14.6743 11.1058 15.5 10.4955Z",stroke:"currentColor",strokeWidth:"1.13793",strokeLinecap:"round",strokeLinejoin:"round"})}),Dp=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,E.jsx)("path",{d:"M11.3799 6.9572L9.05645 4.63375M11.3799 6.9572L6.74949 11.5699C6.61925 11.6996 6.45577 11.791 6.277 11.8339L4.29549 12.3092C3.93194 12.3964 3.60478 12.0683 3.69297 11.705L4.16585 9.75693C4.20893 9.57947 4.29978 9.4172 4.42854 9.28771L9.05645 4.63375M11.3799 6.9572L12.3455 5.98759C12.9839 5.34655 12.9839 4.31002 12.3455 3.66897C11.7033 3.02415 10.6594 3.02415 10.0172 3.66897L9.06126 4.62892L9.05645 4.63375",stroke:"currentColor",strokeWidth:"0.9",strokeLinecap:"round",strokeLinejoin:"round"})}),Bp=({size:e=24})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,E.jsx)("path",{d:"M13.5 4C14.7426 4 15.75 5.00736 15.75 6.25V7H18.5C18.9142 7 19.25 7.33579 19.25 7.75C19.25 8.16421 18.9142 8.5 18.5 8.5H17.9678L17.6328 16.2217C17.61 16.7475 17.5912 17.1861 17.5469 17.543C17.5015 17.9087 17.4225 18.2506 17.2461 18.5723C16.9747 19.0671 16.5579 19.4671 16.0518 19.7168C15.7227 19.8791 15.3772 19.9422 15.0098 19.9717C14.6514 20.0004 14.2126 20 13.6865 20H10.3135C9.78735 20 9.34856 20.0004 8.99023 19.9717C8.62278 19.9422 8.27729 19.8791 7.94824 19.7168C7.44205 19.4671 7.02532 19.0671 6.75391 18.5723C6.57751 18.2506 6.49853 17.9087 6.45312 17.543C6.40883 17.1861 6.39005 16.7475 6.36719 16.2217L6.03223 8.5H5.5C5.08579 8.5 4.75 8.16421 4.75 7.75C4.75 7.33579 5.08579 7 5.5 7H8.25V6.25C8.25 5.00736 9.25736 4 10.5 4H13.5ZM7.86621 16.1562C7.89013 16.7063 7.90624 17.0751 7.94141 17.3584C7.97545 17.6326 8.02151 17.7644 8.06934 17.8516C8.19271 18.0763 8.38239 18.2577 8.6123 18.3711C8.70153 18.4151 8.83504 18.4545 9.11035 18.4766C9.39482 18.4994 9.76335 18.5 10.3135 18.5H13.6865C14.2367 18.5 14.6052 18.4994 14.8896 18.4766C15.165 18.4545 15.2985 18.4151 15.3877 18.3711C15.6176 18.2577 15.8073 18.0763 15.9307 17.8516C15.9785 17.7644 16.0245 17.6326 16.0586 17.3584C16.0938 17.0751 16.1099 16.7063 16.1338 16.1562L16.4668 8.5H7.5332L7.86621 16.1562ZM9.97656 10.75C10.3906 10.7371 10.7371 11.0626 10.75 11.4766L10.875 15.4766C10.8879 15.8906 10.5624 16.2371 10.1484 16.25C9.73443 16.2629 9.38794 15.9374 9.375 15.5234L9.25 11.5234C9.23706 11.1094 9.56255 10.7629 9.97656 10.75ZM14.0244 10.75C14.4383 10.7635 14.7635 11.1105 14.75 11.5244L14.6201 15.5244C14.6066 15.9384 14.2596 16.2634 13.8457 16.25C13.4317 16.2365 13.1067 15.8896 13.1201 15.4756L13.251 11.4756C13.2645 11.0617 13.6105 10.7366 14.0244 10.75ZM10.5 5.5C10.0858 5.5 9.75 5.83579 9.75 6.25V7H14.25V6.25C14.25 5.83579 13.9142 5.5 13.5 5.5H10.5Z",fill:"currentColor"})}),zp=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,E.jsx)("path",{d:"M8.5 3.5L4 8L8.5 12.5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),Sy=({size:e=16})=>(0,E.jsx)("svg",{width:e,height:e,viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,E.jsx)("path",{d:"M8.5 11.5L12 8L8.5 4.5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),My=({size:e=20,color:t="#4C74FF"})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 28 28",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:[(0,E.jsx)("style",{children:`
      @keyframes bunnyEnterEar {
        0% { opacity: 0; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1); }
      }
      @keyframes bunnyEnterFace {
        0% { opacity: 0; transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
      }
      @keyframes bunnyEnterEye {
        0% { opacity: 0; transform: scale(0.5); }
        100% { opacity: 1; transform: scale(1); }
      }
      @keyframes leftEyeLook {
        0%, 8% { transform: translate(0, 0); }
        10%, 18% { transform: translate(1.5px, 0); }
        20%, 22% { transform: translate(1.5px, 0) scaleY(0.1); }
        24%, 32% { transform: translate(1.5px, 0); }
        35%, 48% { transform: translate(-0.8px, -0.6px); }
        52%, 54% { transform: translate(0, 0) scaleY(0.1); }
        56%, 68% { transform: translate(0, 0); }
        72%, 82% { transform: translate(-0.5px, 0.5px); }
        85%, 100% { transform: translate(0, 0); }
      }
      @keyframes rightEyeLook {
        0%, 8% { transform: translate(0, 0); }
        10%, 18% { transform: translate(0.8px, 0); }
        20%, 22% { transform: translate(0.8px, 0) scaleY(0.1); }
        24%, 32% { transform: translate(0.8px, 0); }
        35%, 48% { transform: translate(-1.5px, -0.6px); }
        52%, 54% { transform: translate(0, 0) scaleY(0.1); }
        56%, 68% { transform: translate(0, 0); }
        72%, 82% { transform: translate(-1.2px, 0.5px); }
        85%, 100% { transform: translate(0, 0); }
      }
      @keyframes leftEarTwitch {
        0%, 9% { transform: rotate(0deg); }
        12% { transform: rotate(-8deg); }
        16%, 34% { transform: rotate(0deg); }
        38% { transform: rotate(-12deg); }
        42% { transform: rotate(-6deg); }
        48%, 100% { transform: rotate(0deg); }
      }
      @keyframes rightEarTwitch {
        0%, 9% { transform: rotate(0deg); }
        12% { transform: rotate(6deg); }
        16%, 34% { transform: rotate(0deg); }
        38% { transform: rotate(10deg); }
        42% { transform: rotate(4deg); }
        48%, 71% { transform: rotate(0deg); }
        74% { transform: rotate(8deg); }
        78%, 100% { transform: rotate(0deg); }
      }
      .bunny-eye-left {
        opacity: 0;
        animation: bunnyEnterEye 0.3s ease-out 0.35s forwards, leftEyeLook 5s ease-in-out 0.65s infinite;
        transform-origin: center;
        transform-box: fill-box;
      }
      .bunny-eye-right {
        opacity: 0;
        animation: bunnyEnterEye 0.3s ease-out 0.4s forwards, rightEyeLook 5s ease-in-out 0.7s infinite;
        transform-origin: center;
        transform-box: fill-box;
      }
      .bunny-ear-left {
        opacity: 0;
        animation: bunnyEnterEar 0.3s ease-out 0.1s forwards, leftEarTwitch 5s ease-in-out 0.4s infinite;
        transform-origin: bottom center;
        transform-box: fill-box;
      }
      .bunny-ear-right {
        opacity: 0;
        animation: bunnyEnterEar 0.3s ease-out 0.15s forwards, rightEarTwitch 5s ease-in-out 0.45s infinite;
        transform-origin: bottom center;
        transform-box: fill-box;
      }
      .bunny-face {
        opacity: 0;
        animation: bunnyEnterFace 0.3s ease-out 0.25s forwards;
        transform-origin: center;
        transform-box: fill-box;
      }
      svg:hover .bunny-eye-left,
      svg:hover .bunny-eye-right {
        opacity: 0;
        transition: opacity 0.2s ease;
      }
      .bunny-happy-face {
        opacity: 0;
        transition: opacity 0.2s ease;
      }
      svg:hover .bunny-happy-face {
        opacity: 1;
      }
    `}),(0,E.jsx)("rect",{width:"28",height:"28",fill:"transparent"}),(0,E.jsx)("path",{className:"bunny-ear-left",d:"M3.738 10.2164L7.224 2.007H9.167L5.676 10.2164H3.738ZM10.791 6.42705C10.791 5.90346 10.726 5.42764 10.596 4.99959C10.47 4.57155 10.292 4.16643 10.063 3.78425C9.833 3.39825 9.56 3.01797 9.243 2.64343C8.926 2.26507 8.767 2.07589 8.767 2.07589L10.24 0.957996C10.24 0.957996 10.433 1.17203 10.819 1.60007C11.209 2.0243 11.559 2.49056 11.869 2.99886C12.178 3.50717 12.413 4.04222 12.574 4.60403C12.734 5.16584 12.814 5.77352 12.814 6.42705C12.814 7.10734 12.73 7.7303 12.562 8.29593C12.394 8.85774 12.153 9.3966 11.84 9.9126C11.526 10.4247 11.181 10.8833 10.802 11.2884C10.428 11.6974 10.24 11.9018 10.24 11.9018L8.767 10.7839C8.767 10.7839 8.924 10.5948 9.237 10.2164C9.554 9.8419 9.83 9.4597 10.063 9.06985C10.3 8.6762 10.479 8.26726 10.602 7.84304C10.728 7.41499 10.791 6.943 10.791 6.42705Z",fill:t}),(0,E.jsx)("path",{className:"bunny-ear-right",d:"M15.003 10.2164L18.489 2.007H20.432L16.941 10.2164H15.003ZM22.056 6.42705C22.056 5.90346 21.991 5.42764 21.861 4.99959C21.735 4.57155 21.557 4.16643 21.328 3.78425C21.098 3.39825 20.825 3.01797 20.508 2.64343C20.191 2.26507 20.032 2.07589 20.032 2.07589L21.505 0.957996C21.505 0.957996 21.698 1.17203 22.084 1.60007C22.474 2.0243 22.824 2.49056 23.133 2.99886C23.443 3.50717 23.678 4.04222 23.839 4.60403C23.999 5.16584 24.079 5.77352 24.079 6.42705C24.079 7.10734 23.995 7.7303 23.827 8.29593C23.659 8.85774 23.418 9.3966 23.105 9.9126C22.791 10.4247 22.445 10.8833 22.067 11.2884C21.693 11.6974 21.505 11.9018 21.505 11.9018L20.032 10.7839C20.032 10.7839 20.189 10.5948 20.502 10.2164C20.819 9.8419 21.094 9.4597 21.328 9.06985C21.565 8.6762 21.744 8.26726 21.866 7.84304C21.993 7.41499 22.056 6.943 22.056 6.42705Z",fill:t}),(0,E.jsx)("path",{className:"bunny-face",d:"M2.03 20.4328C2.03 20.9564 2.093 21.4322 2.219 21.8602C2.345 22.2883 2.523 22.6953 2.752 23.0813C2.981 23.4635 3.254 23.8419 3.572 24.2164C3.889 24.5948 4.047 24.7839 4.047 24.7839L2.574 25.9018C2.574 25.9018 2.379 25.6878 1.989 25.2598C1.603 24.8355 1.256 24.3693 0.946 23.861C0.636 23.3527 0.401 22.8176 0.241 22.2558C0.08 21.694 0 21.0863 0 20.4328C0 19.7525 0.084 19.1314 0.252 18.5696C0.421 18.004 0.661 17.4651 0.975 16.953C1.288 16.4371 1.632 15.9765 2.007 15.5714C2.385 15.1625 2.574 14.958 2.574 14.958L4.047 16.0759C4.047 16.0759 3.889 16.2651 3.572 16.6434C3.258 17.018 2.983 17.4021 2.746 17.7957C2.513 18.1855 2.335 18.5945 2.213 19.0225C2.091 19.4467 2.03 19.9168 2.03 20.4328ZM23.687 20.4271C23.687 19.9035 23.622 19.4276 23.492 18.9996C23.366 18.5715 23.188 18.1664 22.959 17.7843C22.729 17.3982 22.456 17.018 22.139 16.6434C21.822 16.2651 21.663 16.0759 21.663 16.0759L23.136 14.958C23.136 14.958 23.329 15.172 23.715 15.6001C24.105 16.0243 24.455 16.4906 24.765 16.9989C25.074 17.5072 25.309 18.0422 25.47 18.604C25.63 19.1658 25.71 19.7735 25.71 20.4271C25.71 21.1073 25.626 21.7303 25.458 22.2959C25.29 22.8577 25.049 23.3966 24.736 23.9126C24.422 24.4247 24.077 24.8833 23.698 25.2884C23.324 25.6974 23.136 25.9018 23.136 25.9018L21.663 24.7839C21.663 24.7839 21.82 24.5948 22.133 24.2164C22.45 23.8419 22.726 23.4597 22.959 23.0698C23.196 22.6762 23.375 22.2673 23.498 21.843C23.624 21.415 23.687 20.943 23.687 20.4271Z",fill:t}),(0,E.jsx)("circle",{className:"bunny-eye-left",cx:"8.277",cy:"20.466",r:"1.8",fill:t}),(0,E.jsx)("circle",{className:"bunny-eye-right",cx:"19.878",cy:"20.466",r:"1.8",fill:t}),(0,E.jsx)("text",{className:"bunny-happy-face",x:"14",y:"26",textAnchor:"middle",fontSize:"12",fontWeight:"bold",fill:t,fontFamily:"system-ui, -apple-system, sans-serif",children:"\u02C3 \u1D55 \u02C2"})]}),Op=({size:e=24})=>(0,E.jsxs)("svg",{width:e,height:e,viewBox:"0 0 24 24",fill:"none",children:[(0,E.jsx)("rect",{x:"3",y:"3",width:"18",height:"18",rx:"2",stroke:"currentColor",strokeWidth:"1.5"}),(0,E.jsx)("line",{x1:"3",y1:"9",x2:"21",y2:"9",stroke:"currentColor",strokeWidth:"1.5"}),(0,E.jsx)("line",{x1:"9",y1:"9",x2:"9",y2:"21",stroke:"currentColor",strokeWidth:"1.5"})]}),Ap=["data-feedback-toolbar","data-annotation-popup","data-annotation-marker"],gu=Ap.flatMap(e=>[`:not([${e}])`,`:not([${e}] *)`]).join(""),Lu="feedback-freeze-styles",yu="__agentation_freeze";function Ey(){if(typeof window>"u")return{frozen:!1,installed:!0,origSetTimeout:setTimeout,origSetInterval:setInterval,origRAF:t=>0,pausedAnimations:[],frozenTimeoutQueue:[],frozenRAFQueue:[]};let e=window;return e[yu]||(e[yu]={frozen:!1,installed:!1,origSetTimeout:null,origSetInterval:null,origRAF:null,pausedAnimations:[],frozenTimeoutQueue:[],frozenRAFQueue:[]}),e[yu]}var Be=Ey();typeof window<"u"&&!Be.installed&&(Be.origSetTimeout=window.setTimeout.bind(window),Be.origSetInterval=window.setInterval.bind(window),Be.origRAF=window.requestAnimationFrame.bind(window),window.setTimeout=(e,t,...n)=>typeof e=="string"?Be.origSetTimeout(e,t):Be.origSetTimeout((...o)=>{Be.frozen?Be.frozenTimeoutQueue.push(()=>e(...o)):e(...o)},t,...n),window.setInterval=(e,t,...n)=>typeof e=="string"?Be.origSetInterval(e,t):Be.origSetInterval((...o)=>{Be.frozen||e(...o)},t,...n),window.requestAnimationFrame=e=>Be.origRAF(t=>{Be.frozen?Be.frozenRAFQueue.push(e):e(t)}),Be.installed=!0);var fe=Be.origSetTimeout,Ly=Be.origSetInterval,kl=Be.origRAF;function Iy(e){return e?Ap.some(t=>!!e.closest?.(`[${t}]`)):!1}function Ny(){if(typeof document>"u"||Be.frozen)return;Be.frozen=!0,Be.frozenTimeoutQueue=[],Be.frozenRAFQueue=[];let e=document.getElementById(Lu);e||(e=document.createElement("style"),e.id=Lu),e.textContent=`
    *${gu},
    *${gu}::before,
    *${gu}::after {
      animation-play-state: paused !important;
      transition: none !important;
    }
  `,document.head.appendChild(e),Be.pausedAnimations=[];try{document.getAnimations().forEach(t=>{if(t.playState!=="running")return;let n=t.effect?.target;Iy(n)||(t.pause(),Be.pausedAnimations.push(t))})}catch{}document.querySelectorAll("video").forEach(t=>{t.paused||(t.dataset.wasPaused="false",t.pause())})}function Gh(){if(typeof document>"u"||!Be.frozen)return;Be.frozen=!1;let e=Be.frozenTimeoutQueue;Be.frozenTimeoutQueue=[];for(let n of e)Be.origSetTimeout(()=>{if(Be.frozen){Be.frozenTimeoutQueue.push(n);return}try{n()}catch(o){console.warn("[agentation] Error replaying queued timeout:",o)}},0);let t=Be.frozenRAFQueue;Be.frozenRAFQueue=[];for(let n of t)Be.origRAF(o=>{if(Be.frozen){Be.frozenRAFQueue.push(n);return}n(o)});for(let n of Be.pausedAnimations)try{n.play()}catch(o){console.warn("[agentation] Error resuming animation:",o)}Be.pausedAnimations=[],document.getElementById(Lu)?.remove(),document.querySelectorAll("video").forEach(n=>{n.dataset.wasPaused==="false"&&(n.play().catch(()=>{}),delete n.dataset.wasPaused)})}function xu(e){if(!e)return;let t=n=>n.stopImmediatePropagation();document.addEventListener("focusin",t,!0),document.addEventListener("focusout",t,!0);try{e.focus()}finally{document.removeEventListener("focusin",t,!0),document.removeEventListener("focusout",t,!0)}}var Di=(0,Ct.forwardRef)(function({element:t,timestamp:n,selectedText:o,placeholder:r="What should change?",initialValue:l="",submitLabel:i="Add",onSubmit:s,onCancel:a,onDelete:m,style:p,accentColor:b="#3c82f7",isExiting:y=!1,lightMode:R=!1,computedStyles:C},N){let[L,f]=(0,Ct.useState)(l),[g,w]=(0,Ct.useState)(!1),[$,U]=(0,Ct.useState)("initial"),[V,B]=(0,Ct.useState)(!1),[q,ye]=(0,Ct.useState)(!1),Z=(0,Ct.useRef)(null),he=(0,Ct.useRef)(null),Ge=(0,Ct.useRef)(null),st=(0,Ct.useRef)(null);(0,Ct.useEffect)(()=>{y&&$!=="exit"&&U("exit")},[y,$]),(0,Ct.useEffect)(()=>{fe(()=>{U("enter")},0);let me=fe(()=>{U("entered")},200),Ye=fe(()=>{let Mt=Z.current;Mt&&(xu(Mt),Mt.selectionStart=Mt.selectionEnd=Mt.value.length,Mt.scrollTop=Mt.scrollHeight)},50);return()=>{clearTimeout(me),clearTimeout(Ye),Ge.current&&clearTimeout(Ge.current),st.current&&clearTimeout(st.current)}},[]);let Re=(0,Ct.useCallback)(()=>{st.current&&clearTimeout(st.current),w(!0),st.current=fe(()=>{w(!1),xu(Z.current)},250)},[]);(0,Ct.useImperativeHandle)(N,()=>({shake:Re}),[Re]);let We=(0,Ct.useCallback)(()=>{U("exit"),Ge.current=fe(()=>{a()},150)},[a]),Ee=(0,Ct.useCallback)(()=>{L.trim()&&s(L.trim())},[L,s]),qe=(0,Ct.useCallback)(me=>{me.stopPropagation(),!me.nativeEvent.isComposing&&(me.key==="Enter"&&!me.shiftKey&&(me.preventDefault(),Ee()),me.key==="Escape"&&We())},[Ee,We]),Q=[ct.popup,R?ct.light:"",$==="enter"?ct.enter:"",$==="entered"?ct.entered:"",$==="exit"?ct.exit:"",g?ct.shake:""].filter(Boolean).join(" ");return(0,yt.jsxs)("div",{ref:he,className:Q,"data-annotation-popup":!0,style:p,onClick:me=>me.stopPropagation(),children:[(0,yt.jsxs)("div",{className:ct.header,children:[C&&Object.keys(C).length>0?(0,yt.jsxs)("button",{className:ct.headerToggle,onClick:()=>{let me=q;ye(!q),me&&fe(()=>xu(Z.current),0)},type:"button",children:[(0,yt.jsx)("svg",{className:`${ct.chevron} ${q?ct.expanded:""}`,width:"14",height:"14",viewBox:"0 0 14 14",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,yt.jsx)("path",{d:"M5.5 10.25L9 7.25L5.75 4",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})}),(0,yt.jsx)("span",{className:ct.element,children:t})]}):(0,yt.jsx)("span",{className:ct.element,children:t}),n&&(0,yt.jsx)("span",{className:ct.timestamp,children:n})]}),C&&Object.keys(C).length>0&&(0,yt.jsx)("div",{className:`${ct.stylesWrapper} ${q?ct.expanded:""}`,children:(0,yt.jsx)("div",{className:ct.stylesInner,children:(0,yt.jsx)("div",{className:ct.stylesBlock,children:Object.entries(C).map(([me,Ye])=>(0,yt.jsxs)("div",{className:ct.styleLine,children:[(0,yt.jsx)("span",{className:ct.styleProperty,children:me.replace(/([A-Z])/g,"-$1").toLowerCase()}),": ",(0,yt.jsx)("span",{className:ct.styleValue,children:Ye}),";"]},me))})})}),o&&(0,yt.jsxs)("div",{className:ct.quote,children:["\u201C",o.slice(0,80),o.length>80?"...":"","\u201D"]}),(0,yt.jsx)("textarea",{ref:Z,className:ct.textarea,style:{borderColor:V?b:void 0},placeholder:r,value:L,onChange:me=>f(me.target.value),onFocus:()=>B(!0),onBlur:()=>B(!1),rows:2,onKeyDown:qe}),(0,yt.jsxs)("div",{className:ct.actions,children:[m&&(0,yt.jsx)("div",{className:ct.deleteWrapper,children:(0,yt.jsx)("button",{className:ct.deleteButton,onClick:m,type:"button",children:(0,yt.jsx)(Bp,{size:22})})}),(0,yt.jsx)("button",{className:ct.cancel,onClick:We,children:"Cancel"}),(0,yt.jsx)("button",{className:ct.submit,style:{backgroundColor:b,opacity:L.trim()?1:.4},onClick:Ee,disabled:!L.trim(),children:i})]})]})}),$y=({content:e,children:t,...n})=>{let[o,r]=(0,po.useState)(!1),[l,i]=(0,po.useState)(!1),[s,a]=(0,po.useState)({top:0,right:0}),m=(0,po.useRef)(null),p=(0,po.useRef)(null),b=(0,po.useRef)(null),y=()=>{if(m.current){let N=m.current.getBoundingClientRect();a({top:N.top+N.height/2,right:window.innerWidth-N.left+8})}},R=()=>{i(!0),b.current&&(clearTimeout(b.current),b.current=null),y(),p.current=fe(()=>{r(!0)},500)},C=()=>{p.current&&(clearTimeout(p.current),p.current=null),r(!1),b.current=fe(()=>{i(!1)},150)};return(0,po.useEffect)(()=>()=>{p.current&&clearTimeout(p.current),b.current&&clearTimeout(b.current)},[]),(0,Rr.jsxs)(Rr.Fragment,{children:[(0,Rr.jsx)("span",{ref:m,onMouseEnter:R,onMouseLeave:C,...n,children:t}),l&&(0,Wp.createPortal)((0,Rr.jsx)("div",{"data-feedback-toolbar":!0,style:{position:"fixed",top:s.top,right:s.right,transform:"translateY(-50%)",padding:"6px 10px",background:"#383838",color:"rgba(255, 255, 255, 0.7)",fontSize:"11px",fontWeight:400,lineHeight:"14px",borderRadius:"10px",width:"180px",textAlign:"left",zIndex:100020,pointerEvents:"none",boxShadow:"0px 1px 8px rgba(0, 0, 0, 0.28)",opacity:o?1:0,transition:"opacity 0.15s ease"},children:e}),document.body)]})},Ry=`.styles-module__tooltip___mcXL2 {
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: help;
}

.styles-module__tooltipIcon___Nq2nD {
  transform: translateY(0.5px);
  color: #fff;
  opacity: 0.2;
  transition: opacity 0.15s ease;
  will-change: transform;
}
.styles-module__tooltip___mcXL2:hover .styles-module__tooltipIcon___Nq2nD {
  opacity: 0.5;
}
[data-agentation-theme=light] .styles-module__tooltipIcon___Nq2nD {
  color: #000;
}`,Py={tooltip:"styles-module__tooltip___mcXL2",tooltipIcon:"styles-module__tooltipIcon___Nq2nD"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-help-tooltip-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-help-tooltip-styles",document.head.appendChild(e)),e.textContent=Ry}var Zh=Py,Nr=({content:e})=>(0,Iu.jsx)($y,{className:Zh.tooltip,content:e,children:(0,Iu.jsx)(Sp,{className:Zh.tooltipIcon})}),ee={navigation:{width:800,height:56},hero:{width:800,height:320},header:{width:800,height:80},section:{width:800,height:400},sidebar:{width:240,height:400},footer:{width:800,height:160},modal:{width:480,height:300},card:{width:280,height:240},text:{width:400,height:120},image:{width:320,height:200},video:{width:480,height:270},table:{width:560,height:220},grid:{width:600,height:300},list:{width:300,height:180},chart:{width:400,height:240},button:{width:140,height:40},input:{width:280,height:56},form:{width:360,height:320},tabs:{width:480,height:240},dropdown:{width:200,height:200},toggle:{width:44,height:24},search:{width:320,height:44},avatar:{width:48,height:48},badge:{width:80,height:28},breadcrumb:{width:300,height:24},pagination:{width:300,height:36},progress:{width:240,height:8},divider:{width:600,height:1},accordion:{width:400,height:200},carousel:{width:600,height:300},toast:{width:320,height:64},tooltip:{width:180,height:40},pricing:{width:300,height:360},testimonial:{width:360,height:200},cta:{width:600,height:160},alert:{width:400,height:56},banner:{width:800,height:48},stat:{width:200,height:120},stepper:{width:480,height:48},tag:{width:72,height:28},rating:{width:160,height:28},map:{width:480,height:300},timeline:{width:360,height:320},fileUpload:{width:360,height:180},codeBlock:{width:480,height:200},calendar:{width:300,height:300},notification:{width:360,height:72},productCard:{width:280,height:360},profile:{width:280,height:200},drawer:{width:320,height:400},popover:{width:240,height:160},logo:{width:120,height:40},faq:{width:560,height:320},gallery:{width:560,height:360},checkbox:{width:20,height:20},radio:{width:20,height:20},slider:{width:240,height:32},datePicker:{width:300,height:320},skeleton:{width:320,height:120},chip:{width:96,height:32},icon:{width:24,height:24},spinner:{width:32,height:32},feature:{width:360,height:200},team:{width:560,height:280},login:{width:360,height:360},contact:{width:400,height:320}},Fp=[{section:"Layout",items:[{type:"navigation",label:"Navigation",...ee.navigation},{type:"header",label:"Header",...ee.header},{type:"hero",label:"Hero",...ee.hero},{type:"section",label:"Section",...ee.section},{type:"sidebar",label:"Sidebar",...ee.sidebar},{type:"footer",label:"Footer",...ee.footer},{type:"modal",label:"Modal",...ee.modal},{type:"banner",label:"Banner",...ee.banner},{type:"drawer",label:"Drawer",...ee.drawer},{type:"popover",label:"Popover",...ee.popover},{type:"divider",label:"Divider",...ee.divider}]},{section:"Content",items:[{type:"card",label:"Card",...ee.card},{type:"text",label:"Text",...ee.text},{type:"image",label:"Image",...ee.image},{type:"video",label:"Video",...ee.video},{type:"table",label:"Table",...ee.table},{type:"grid",label:"Grid",...ee.grid},{type:"list",label:"List",...ee.list},{type:"chart",label:"Chart",...ee.chart},{type:"codeBlock",label:"Code Block",...ee.codeBlock},{type:"map",label:"Map",...ee.map},{type:"timeline",label:"Timeline",...ee.timeline},{type:"calendar",label:"Calendar",...ee.calendar},{type:"accordion",label:"Accordion",...ee.accordion},{type:"carousel",label:"Carousel",...ee.carousel},{type:"logo",label:"Logo",...ee.logo},{type:"faq",label:"FAQ",...ee.faq},{type:"gallery",label:"Gallery",...ee.gallery}]},{section:"Controls",items:[{type:"button",label:"Button",...ee.button},{type:"input",label:"Input",...ee.input},{type:"search",label:"Search",...ee.search},{type:"form",label:"Form",...ee.form},{type:"tabs",label:"Tabs",...ee.tabs},{type:"dropdown",label:"Dropdown",...ee.dropdown},{type:"toggle",label:"Toggle",...ee.toggle},{type:"stepper",label:"Stepper",...ee.stepper},{type:"rating",label:"Rating",...ee.rating},{type:"fileUpload",label:"File Upload",...ee.fileUpload},{type:"checkbox",label:"Checkbox",...ee.checkbox},{type:"radio",label:"Radio",...ee.radio},{type:"slider",label:"Slider",...ee.slider},{type:"datePicker",label:"Date Picker",...ee.datePicker}]},{section:"Elements",items:[{type:"avatar",label:"Avatar",...ee.avatar},{type:"badge",label:"Badge",...ee.badge},{type:"tag",label:"Tag",...ee.tag},{type:"breadcrumb",label:"Breadcrumb",...ee.breadcrumb},{type:"pagination",label:"Pagination",...ee.pagination},{type:"progress",label:"Progress",...ee.progress},{type:"alert",label:"Alert",...ee.alert},{type:"toast",label:"Toast",...ee.toast},{type:"notification",label:"Notification",...ee.notification},{type:"tooltip",label:"Tooltip",...ee.tooltip},{type:"stat",label:"Stat",...ee.stat},{type:"skeleton",label:"Skeleton",...ee.skeleton},{type:"chip",label:"Chip",...ee.chip},{type:"icon",label:"Icon",...ee.icon},{type:"spinner",label:"Spinner",...ee.spinner}]},{section:"Blocks",items:[{type:"pricing",label:"Pricing",...ee.pricing},{type:"testimonial",label:"Testimonial",...ee.testimonial},{type:"cta",label:"CTA",...ee.cta},{type:"productCard",label:"Product Card",...ee.productCard},{type:"profile",label:"Profile",...ee.profile},{type:"feature",label:"Feature",...ee.feature},{type:"team",label:"Team",...ee.team},{type:"login",label:"Login",...ee.login},{type:"contact",label:"Contact",...ee.contact}]}],Jn={};for(let e of Fp)for(let t of e.items)Jn[t.type]=t;function O({w:e,h:t=3,strong:n}){return(0,d.jsx)("div",{style:{width:typeof e=="number"?`${e}px`:e,height:t,borderRadius:2,background:n?"var(--agd-bar-strong)":"var(--agd-bar)",flexShrink:0}})}function it({w:e,h:t,radius:n=3,style:o}){return(0,d.jsx)("div",{style:{width:typeof e=="number"?`${e}px`:e,height:typeof t=="number"?`${t}px`:t,borderRadius:n,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",flexShrink:0,...o}})}function an({size:e}){return(0,d.jsx)("div",{style:{width:e,height:e,borderRadius:"50%",border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",flexShrink:0}})}function Ty({width:e,height:t}){let n=Math.max(8,t*.2);return(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",height:"100%",padding:`0 ${n}px`,gap:e*.02},children:[(0,d.jsx)(it,{w:Math.max(20,t*.5),h:Math.max(12,t*.4),radius:2}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",gap:e*.03,marginLeft:e*.04},children:[(0,d.jsx)(O,{w:e*.06}),(0,d.jsx)(O,{w:e*.07}),(0,d.jsx)(O,{w:e*.05}),(0,d.jsx)(O,{w:e*.06})]}),(0,d.jsx)(it,{w:e*.1,h:Math.min(28,t*.5),radius:4})]})}function Dy({width:e,height:t,text:n}){return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:"100%",gap:t*.05},children:[n?(0,d.jsx)("span",{style:{fontSize:Math.min(20,t*.08),fontWeight:600,color:"var(--agd-text-3)",textAlign:"center",maxWidth:"80%"},children:n}):(0,d.jsx)(O,{w:e*.5,h:Math.max(6,t*.04),strong:!0}),(0,d.jsx)(O,{w:e*.6}),(0,d.jsx)(O,{w:e*.4}),(0,d.jsx)(it,{w:Math.min(140,e*.2),h:Math.min(36,t*.12),radius:6,style:{marginTop:t*.06}})]})}function By({width:e,height:t}){let n=Math.max(3,Math.floor(t/36));return(0,d.jsxs)("div",{style:{padding:e*.08,display:"flex",flexDirection:"column",gap:t*.03},children:[(0,d.jsx)(O,{w:e*.6,h:4,strong:!0}),Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:6},children:[(0,d.jsx)(it,{w:10,h:10,radius:2}),(0,d.jsx)(O,{w:e*(.4+r*17%30/100)})]},r))]})}function zy({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/160)));return(0,d.jsx)("div",{style:{display:"flex",padding:`${t*.12}px ${e*.03}px`,gap:e*.05},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsx)(O,{w:"60%",h:3,strong:!0}),(0,d.jsx)(O,{w:"80%",h:2}),(0,d.jsx)(O,{w:"70%",h:2}),(0,d.jsx)(O,{w:"60%",h:2})]},r))})}function Oy({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsxs)("div",{style:{padding:"10px 12px",borderBottom:"1px solid var(--agd-stroke)",display:"flex",alignItems:"center",justifyContent:"space-between"},children:[(0,d.jsx)(O,{w:e*.3,h:4,strong:!0}),(0,d.jsx)("div",{style:{width:14,height:14,border:"1px solid var(--agd-stroke)",borderRadius:3}})]}),(0,d.jsxs)("div",{style:{flex:1,padding:12,display:"flex",flexDirection:"column",gap:6},children:[(0,d.jsx)(O,{w:"90%"}),(0,d.jsx)(O,{w:"70%"}),(0,d.jsx)(O,{w:"80%"})]}),(0,d.jsxs)("div",{style:{padding:"10px 12px",borderTop:"1px solid var(--agd-stroke)",display:"flex",justifyContent:"flex-end",gap:8},children:[(0,d.jsx)(it,{w:70,h:26,radius:4}),(0,d.jsx)(it,{w:70,h:26,radius:4,style:{background:"var(--agd-bar)"}})]})]})}function Ay({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsx)("div",{style:{height:"40%",background:"var(--agd-fill)",borderBottom:"1px dashed var(--agd-stroke)"}}),(0,d.jsxs)("div",{style:{flex:1,padding:10,display:"flex",flexDirection:"column",gap:5},children:[(0,d.jsx)(O,{w:"70%",h:4,strong:!0}),(0,d.jsx)(O,{w:"95%",h:2}),(0,d.jsx)(O,{w:"85%",h:2}),(0,d.jsx)(O,{w:"50%",h:2})]})]})}function Wy({width:e,height:t,text:n}){if(n)return(0,d.jsx)("div",{style:{padding:4,fontSize:Math.min(14,t*.3),lineHeight:1.5,color:"var(--agd-text-3)",wordBreak:"break-word",overflow:"hidden"},children:n});let o=Math.max(2,Math.floor(t/18));return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:6,padding:4},children:[(0,d.jsx)(O,{w:e*.6,h:5,strong:!0}),Array.from({length:o},(r,l)=>(0,d.jsx)(O,{w:`${70+l*13%25}%`,h:2},l))]})}function Fy({width:e,height:t}){return(0,d.jsx)("div",{style:{height:"100%",position:"relative"},children:(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,preserveAspectRatio:"none",fill:"none",children:[(0,d.jsx)("line",{x1:"0",y1:"0",x2:e,y2:t,stroke:"var(--agd-stroke)",strokeWidth:"1"}),(0,d.jsx)("line",{x1:e,y1:"0",x2:"0",y2:t,stroke:"var(--agd-stroke)",strokeWidth:"1"}),(0,d.jsx)("circle",{cx:e*.3,cy:t*.3,r:Math.min(e,t)*.08,fill:"var(--agd-fill)",stroke:"var(--agd-stroke)",strokeWidth:"0.8"})]})})}function jy({width:e,height:t}){let n=Math.max(2,Math.min(5,Math.floor(e/100))),o=Math.max(2,Math.min(6,Math.floor(t/32)));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsx)("div",{style:{display:"flex",borderBottom:"1px solid var(--agd-stroke)",padding:"6px 0"},children:Array.from({length:n},(r,l)=>(0,d.jsx)("div",{style:{flex:1,padding:"0 8px"},children:(0,d.jsx)(O,{w:"70%",h:3,strong:!0})},l))}),Array.from({length:o},(r,l)=>(0,d.jsx)("div",{style:{display:"flex",borderBottom:"1px solid rgba(255,255,255,0.03)",padding:"6px 0"},children:Array.from({length:n},(i,s)=>(0,d.jsx)("div",{style:{flex:1,padding:"0 8px"},children:(0,d.jsx)(O,{w:`${50+(l*7+s*13)%40}%`,h:2})},s))},l))]})}function Hy({width:e,height:t}){let n=Math.max(2,Math.floor(t/28));return(0,d.jsx)("div",{style:{display:"flex",flexDirection:"column",gap:4,padding:4},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:8,padding:"4px 0"},children:[(0,d.jsx)(an,{size:8}),(0,d.jsx)(O,{w:`${55+r*17%35}%`,h:2})]},r))})}function Uy({width:e,height:t,text:n}){return(0,d.jsx)("div",{style:{height:"100%",borderRadius:Math.min(8,t/3),border:"1px solid var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center"},children:n?(0,d.jsx)("span",{style:{fontSize:Math.min(13,t*.4),fontWeight:500,color:"var(--agd-text-3)",letterSpacing:"-0.01em"},children:n}):(0,d.jsx)(O,{w:Math.max(20,e*.5),h:3,strong:!0})})}function Yy({width:e,height:t}){return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:4,height:"100%",justifyContent:"center"},children:[(0,d.jsx)(O,{w:Math.min(80,e*.3),h:2}),(0,d.jsx)("div",{style:{height:Math.min(36,t*.6),borderRadius:4,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",paddingLeft:8},children:(0,d.jsx)(O,{w:"40%",h:2})})]})}function Xy({width:e,height:t}){let n=Math.max(2,Math.min(5,Math.floor(t/56)));return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:t*.04,padding:8},children:[Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsx)(O,{w:60+r*17%30,h:2}),(0,d.jsx)(it,{w:"100%",h:28,radius:4})]},r)),(0,d.jsx)(it,{w:Math.min(120,e*.35),h:30,radius:6,style:{marginTop:8,alignSelf:"flex-end",background:"var(--agd-bar)"}})]})}function Qy({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/120)));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsx)("div",{style:{display:"flex",gap:2,borderBottom:"1px solid var(--agd-stroke)"},children:Array.from({length:n},(o,r)=>(0,d.jsx)("div",{style:{padding:"8px 12px",borderBottom:r===0?"2px solid var(--agd-bar-strong)":"none"},children:(0,d.jsx)(O,{w:60,h:3,strong:r===0})},r))}),(0,d.jsxs)("div",{style:{flex:1,padding:12,display:"flex",flexDirection:"column",gap:6},children:[(0,d.jsx)(O,{w:"80%",h:2}),(0,d.jsx)(O,{w:"65%",h:2}),(0,d.jsx)(O,{w:"75%",h:2})]})]})}function Vy({width:e,height:t}){let n=Math.min(e,t)/2;return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("circle",{cx:e/2,cy:t/2,r:n-1,stroke:"var(--agd-stroke)",fill:"var(--agd-fill)",strokeWidth:"1.5",strokeDasharray:"3 2"}),(0,d.jsx)("circle",{cx:e/2,cy:t*.38,r:n*.28,stroke:"var(--agd-stroke)",fill:"var(--agd-fill)",strokeWidth:"0.8"}),(0,d.jsx)("path",{d:`M${e/2-n*.55} ${t*.78} C${e/2-n*.55} ${t*.55} ${e/2+n*.55} ${t*.55} ${e/2+n*.55} ${t*.78}`,stroke:"var(--agd-stroke)",fill:"var(--agd-fill)",strokeWidth:"0.8"})]})}function Ky({width:e,height:t}){return(0,d.jsx)("div",{style:{height:"100%",borderRadius:t/2,border:"1px solid var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)(O,{w:Math.max(16,e*.5),h:2,strong:!0})})}function qy({width:e,height:t}){return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:"100%",gap:t*.08},children:[(0,d.jsx)(O,{w:e*.5,h:Math.max(5,t*.06),strong:!0}),(0,d.jsx)(O,{w:e*.35})]})}function Gy({width:e,height:t}){return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",height:"100%",gap:t*.04,padding:e*.04},children:[(0,d.jsx)(O,{w:e*.3,h:4,strong:!0}),(0,d.jsx)(O,{w:e*.7}),(0,d.jsx)(O,{w:e*.5}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",gap:e*.03,marginTop:t*.06},children:[(0,d.jsx)(it,{w:"33%",h:"100%",radius:4}),(0,d.jsx)(it,{w:"33%",h:"100%",radius:4}),(0,d.jsx)(it,{w:"33%",h:"100%",radius:4})]})]})}function Zy({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/140))),o=Math.max(1,Math.min(3,Math.floor(t/120)));return(0,d.jsx)("div",{style:{display:"grid",gridTemplateColumns:`repeat(${n}, 1fr)`,gridTemplateRows:`repeat(${o}, 1fr)`,gap:6,height:"100%"},children:Array.from({length:n*o},(r,l)=>(0,d.jsx)(it,{w:"100%",h:"100%",radius:4},l))})}function Jy({width:e,height:t}){let n=Math.max(2,Math.floor((t-32)/28));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsx)("div",{style:{padding:"6px 8px",borderBottom:"1px solid var(--agd-stroke)"},children:(0,d.jsx)(O,{w:e*.5,h:3,strong:!0})}),(0,d.jsx)("div",{style:{flex:1,padding:4,display:"flex",flexDirection:"column",gap:2},children:Array.from({length:n},(o,r)=>(0,d.jsx)("div",{style:{padding:"4px 6px",borderRadius:3,background:r===0?"var(--agd-fill)":"transparent"},children:(0,d.jsx)(O,{w:`${50+r*17%35}%`,h:2,strong:r===0})},r))})]})}function e5({width:e,height:t}){let n=Math.min(e,t)/2;return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("rect",{x:"1",y:"1",width:e-2,height:t-2,rx:n,stroke:"var(--agd-stroke)",strokeWidth:"1"}),(0,d.jsx)("circle",{cx:e-n,cy:t/2,r:n*.7,fill:"var(--agd-bar)"})]})}function t5({width:e,height:t}){let n=Math.min(t/2,20);return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:n,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:`0 ${n*.6}px`,gap:6},children:[(0,d.jsx)(an,{size:Math.min(14,t*.4)}),(0,d.jsx)(O,{w:"50%",h:2})]})}function n5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:8,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:"0 10px",gap:8},children:[(0,d.jsx)(an,{size:Math.min(20,t*.5)}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:"60%",h:3,strong:!0}),(0,d.jsx)(O,{w:"80%",h:2})]}),(0,d.jsx)("div",{style:{width:14,height:14,border:"1px solid var(--agd-stroke)",borderRadius:3,flexShrink:0}})]})}function o5({width:e,height:t}){return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("rect",{x:"0",y:"0",width:e,height:t,rx:t/2,stroke:"var(--agd-stroke)",strokeWidth:"0.8"}),(0,d.jsx)("rect",{x:"1",y:"1",width:e*.65,height:t-2,rx:(t-2)/2,fill:"var(--agd-bar)"})]})}function r5({width:e,height:t}){let n=Math.max(3,Math.min(7,Math.floor(e/50))),o=e/(n*2);return(0,d.jsx)("div",{style:{height:"100%",display:"flex",alignItems:"flex-end",justifyContent:"space-around",padding:"0 4px",borderBottom:"1px solid var(--agd-stroke)"},children:Array.from({length:n},(r,l)=>{let i=30+(l*37+17)%55;return(0,d.jsx)(it,{w:o,h:`${i}%`,radius:2},l)})})}function l5({width:e,height:t}){let n=Math.min(e,t)*.12;return(0,d.jsxs)("div",{style:{height:"100%",position:"relative",display:"flex",alignItems:"center",justifyContent:"center"},children:[(0,d.jsx)(it,{w:"100%",h:"100%",radius:4}),(0,d.jsx)("div",{style:{position:"absolute",width:n*2,height:n*2,borderRadius:"50%",border:"1.5px solid var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)("div",{style:{width:0,height:0,borderLeft:`${n*.6}px solid var(--agd-bar-strong)`,borderTop:`${n*.4}px solid transparent`,borderBottom:`${n*.4}px solid transparent`,marginLeft:n*.15}})})]})}function i5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center"},children:[(0,d.jsx)("div",{style:{flex:1,width:"100%",borderRadius:6,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)(O,{w:"60%",h:2})}),(0,d.jsx)("div",{style:{width:8,height:8,background:"var(--agd-fill)",border:"1px dashed var(--agd-stroke)",borderTop:"none",borderLeft:"none",transform:"rotate(45deg)",marginTop:-5}})]})}function s5({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/80)));return(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",height:"100%",gap:4},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:4},children:[r>0&&(0,d.jsx)("span",{style:{color:"var(--agd-stroke)",fontSize:10},children:"/"}),(0,d.jsx)(O,{w:40+r*13%20,h:2,strong:r===n-1})]},r))})}function a5({width:e,height:t}){let n=Math.max(3,Math.min(5,Math.floor(e/40))),o=Math.min(28,t*.8);return(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"center",height:"100%",gap:4},children:Array.from({length:n},(r,l)=>(0,d.jsx)(it,{w:o,h:o,radius:4,style:l===1?{background:"var(--agd-bar)"}:void 0},l))})}function c5({width:e}){return(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",height:"100%"},children:(0,d.jsx)("div",{style:{width:"100%",height:1,background:"var(--agd-stroke)"}})})}function d5({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(t/40)));return(0,d.jsx)("div",{style:{display:"flex",flexDirection:"column",height:"100%"},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{borderBottom:"1px solid var(--agd-stroke)",padding:"8px 6px",display:"flex",alignItems:"center",justifyContent:"space-between",flex:r===0?2:1},children:[(0,d.jsx)(O,{w:`${40+r*17%25}%`,h:3,strong:!0}),(0,d.jsx)("span",{style:{fontSize:8,color:"var(--agd-stroke)"},children:r===0?"\u25BC":"\u25B6"})]},r))})}function u5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",gap:6},children:[(0,d.jsxs)("div",{style:{flex:1,display:"flex",gap:6,alignItems:"center"},children:[(0,d.jsx)("span",{style:{fontSize:12,color:"var(--agd-stroke)"},children:"\u2039"}),(0,d.jsx)(it,{w:"100%",h:"100%",radius:4}),(0,d.jsx)("span",{style:{fontSize:12,color:"var(--agd-stroke)"},children:"\u203A"})]}),(0,d.jsxs)("div",{style:{display:"flex",justifyContent:"center",gap:4},children:[(0,d.jsx)(an,{size:5}),(0,d.jsx)(an,{size:5}),(0,d.jsx)(an,{size:5})]})]})}function _5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center",padding:10,gap:t*.04},children:[(0,d.jsx)(O,{w:e*.4,h:3,strong:!0}),(0,d.jsx)(O,{w:e*.3,h:6,strong:!0}),(0,d.jsx)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:4,width:"100%",padding:"8px 0"},children:Array.from({length:4},(n,o)=>(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:4},children:[(0,d.jsx)(an,{size:5}),(0,d.jsx)(O,{w:`${50+o*17%35}%`,h:2})]},o))}),(0,d.jsx)(it,{w:e*.7,h:Math.min(32,t*.1),radius:6,style:{background:"var(--agd-bar)"}})]})}function f5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",padding:10,gap:8},children:[(0,d.jsx)("span",{style:{fontSize:18,lineHeight:1,color:"var(--agd-stroke)",fontFamily:"serif"},children:"\u201C"}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsx)(O,{w:"90%",h:2}),(0,d.jsx)(O,{w:"75%",h:2}),(0,d.jsx)(O,{w:"60%",h:2})]}),(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:6},children:[(0,d.jsx)(an,{size:20}),(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:2},children:[(0,d.jsx)(O,{w:60,h:3,strong:!0}),(0,d.jsx)(O,{w:40,h:2})]})]})]})}function h5({width:e,height:t}){return(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:"100%",gap:t*.08},children:[(0,d.jsx)(O,{w:e*.5,h:Math.max(4,t*.05),strong:!0}),(0,d.jsx)(O,{w:e*.35}),(0,d.jsx)(it,{w:Math.min(140,e*.25),h:Math.min(32,t*.15),radius:6,style:{marginTop:t*.04,background:"var(--agd-bar)"}})]})}function p5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:6,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:"0 10px",gap:8},children:[(0,d.jsx)("div",{style:{width:16,height:16,borderRadius:"50%",border:"1.5px solid var(--agd-bar-strong)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0},children:(0,d.jsx)("div",{style:{width:2,height:6,background:"var(--agd-bar-strong)",borderRadius:1}})}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:"40%",h:3,strong:!0}),(0,d.jsx)(O,{w:"70%",h:2})]})]})}function m5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"0 12px"},children:[(0,d.jsx)(O,{w:e*.4,h:3,strong:!0}),(0,d.jsx)(it,{w:60,h:Math.min(24,t*.6),radius:4})]})}function g5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:t*.06},children:[(0,d.jsx)(O,{w:e*.5,h:2}),(0,d.jsx)(O,{w:e*.4,h:Math.max(8,t*.18),strong:!0}),(0,d.jsx)(O,{w:e*.3,h:2})]})}function y5({width:e,height:t}){let n=Math.max(3,Math.min(5,Math.floor(e/100))),o=Math.min(12,t*.35);return(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"space-between",height:"100%",padding:"0 8px"},children:Array.from({length:n},(r,l)=>(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:0,flex:1},children:[(0,d.jsx)("div",{style:{width:o,height:o,borderRadius:"50%",border:"1.5px solid var(--agd-stroke)",background:l===0?"var(--agd-bar)":"transparent",flexShrink:0}}),l<n-1&&(0,d.jsx)("div",{style:{flex:1,height:1,background:"var(--agd-stroke)",margin:"0 4px"}})]},l))})}function x5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:4,border:"1px solid var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",justifyContent:"center",gap:4,padding:"0 6px"},children:[(0,d.jsx)(O,{w:Math.max(16,e*.5),h:2,strong:!0}),(0,d.jsx)("div",{style:{width:8,height:8,borderRadius:"50%",border:"1px solid var(--agd-stroke)",flexShrink:0}})]})}function v5({width:e,height:t}){let o=Math.min(t*.7,e/7.5);return(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"center",height:"100%",gap:o*.2},children:Array.from({length:5},(r,l)=>(0,d.jsx)("svg",{width:o,height:o,viewBox:"0 0 16 16",fill:"none",children:(0,d.jsx)("path",{d:"M8 1.5l2 4 4.5.7-3.25 3.1.75 4.5L8 11.4l-4 2.4.75-4.5L1.5 6.2 6 5.5z",stroke:"var(--agd-stroke)",strokeWidth:"0.8",fill:l<3?"var(--agd-bar)":"none"})},l))})}function w5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",position:"relative",borderRadius:4,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",overflow:"hidden"},children:[(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",style:{position:"absolute",inset:0},children:[(0,d.jsx)("line",{x1:0,y1:t*.3,x2:e,y2:t*.7,stroke:"var(--agd-stroke)",strokeWidth:"0.5",opacity:".2"}),(0,d.jsx)("line",{x1:0,y1:t*.6,x2:e,y2:t*.2,stroke:"var(--agd-stroke)",strokeWidth:"0.5",opacity:".15"}),(0,d.jsx)("line",{x1:e*.4,y1:0,x2:e*.6,y2:t,stroke:"var(--agd-stroke)",strokeWidth:"0.5",opacity:".15"})]}),(0,d.jsx)("div",{style:{position:"absolute",left:"50%",top:"40%",transform:"translate(-50%, -100%)"},children:(0,d.jsxs)("svg",{width:"16",height:"22",viewBox:"0 0 16 22",fill:"none",children:[(0,d.jsx)("path",{d:"M8 0C3.6 0 0 3.6 0 8c0 6 8 14 8 14s8-8 8-14c0-4.4-3.6-8-8-8z",fill:"var(--agd-bar)",opacity:".4"}),(0,d.jsx)("circle",{cx:"8",cy:"8",r:"3",fill:"var(--agd-fill)"})]})})]})}function b5({width:e,height:t}){let n=Math.max(3,Math.min(5,Math.floor(t/60)));return(0,d.jsxs)("div",{style:{display:"flex",height:"100%",padding:"8px 0"},children:[(0,d.jsx)("div",{style:{width:16,display:"flex",flexDirection:"column",alignItems:"center"},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",flex:1},children:[(0,d.jsx)(an,{size:8}),r<n-1&&(0,d.jsx)("div",{style:{flex:1,width:1,background:"var(--agd-stroke)"}})]},r))}),(0,d.jsx)("div",{style:{flex:1,display:"flex",flexDirection:"column",justifyContent:"space-around",paddingLeft:8},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:`${35+r*13%25}%`,h:3,strong:!0}),(0,d.jsx)(O,{w:`${50+r*17%30}%`,h:2})]},r))})]})}function k5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:8,border:"2px dashed var(--agd-stroke)",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:t*.06},children:[(0,d.jsxs)("svg",{width:"24",height:"24",viewBox:"0 0 24 24",fill:"none",children:[(0,d.jsx)("path",{d:"M12 16V4m0 0l-4 4m4-4l4 4",stroke:"var(--agd-stroke)",strokeWidth:"1.5"}),(0,d.jsx)("path",{d:"M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2",stroke:"var(--agd-stroke)",strokeWidth:"1.5"})]}),(0,d.jsx)(O,{w:e*.4,h:2}),(0,d.jsx)(O,{w:e*.25,h:2})]})}function C5({width:e,height:t}){let n=Math.max(3,Math.min(8,Math.floor(t/20)));return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:6,background:"var(--agd-fill)",border:"1px solid var(--agd-stroke)",padding:8,display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsxs)("div",{style:{display:"flex",gap:3,marginBottom:4},children:[(0,d.jsx)(an,{size:6}),(0,d.jsx)(an,{size:6}),(0,d.jsx)(an,{size:6})]}),Array.from({length:n},(o,r)=>(0,d.jsx)("div",{style:{display:"flex",gap:6,paddingLeft:r>0&&r<n-1?12:0},children:(0,d.jsx)(O,{w:`${25+r*23%50}%`,h:2,strong:r===0})},r))]})}function S5({width:e,height:t}){let r=Math.min((e-16)/7,(t-40)/6);return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"6px 8px"},children:[(0,d.jsx)("span",{style:{fontSize:8,color:"var(--agd-stroke)"},children:"\u2039"}),(0,d.jsx)(O,{w:e*.3,h:3,strong:!0}),(0,d.jsx)("span",{style:{fontSize:8,color:"var(--agd-stroke)"},children:"\u203A"})]}),(0,d.jsxs)("div",{style:{display:"grid",gridTemplateColumns:"repeat(7, 1fr)",gap:2,padding:"0 4px",flex:1},children:[Array.from({length:7},(l,i)=>(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"center",height:r*.6},children:(0,d.jsx)(O,{w:r*.5,h:2})},`h${i}`)),Array.from({length:35},(l,i)=>(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"center",height:r},children:(0,d.jsx)("div",{style:{width:r*.6,height:r*.6,borderRadius:"50%",background:i===12?"var(--agd-bar)":"transparent",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)("div",{style:{width:2,height:2,borderRadius:1,background:"var(--agd-bar-strong)",opacity:i===12?1:.3}})})},i))]})]})}function M5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",borderRadius:8,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:"0 10px",gap:8},children:[(0,d.jsx)(an,{size:Math.min(32,t*.55)}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:"50%",h:3,strong:!0}),(0,d.jsx)(O,{w:"75%",h:2})]}),(0,d.jsx)(O,{w:30,h:2})]})}function E5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column"},children:[(0,d.jsx)("div",{style:{height:"50%",background:"var(--agd-fill)",borderBottom:"1px dashed var(--agd-stroke)"}}),(0,d.jsxs)("div",{style:{flex:1,padding:10,display:"flex",flexDirection:"column",gap:5},children:[(0,d.jsx)(O,{w:"65%",h:4,strong:!0}),(0,d.jsx)(O,{w:"40%",h:3}),(0,d.jsx)("div",{style:{flex:1}}),(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",justifyContent:"space-between"},children:[(0,d.jsx)(O,{w:"30%",h:5,strong:!0}),(0,d.jsx)(it,{w:Math.min(70,e*.3),h:26,radius:4,style:{background:"var(--agd-bar)"}})]})]})]})}function L5({width:e,height:t}){let n=Math.min(48,t*.3);return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:t*.06},children:[(0,d.jsx)(an,{size:n}),(0,d.jsx)(O,{w:e*.45,h:4,strong:!0}),(0,d.jsx)(O,{w:e*.3,h:2}),(0,d.jsxs)("div",{style:{display:"flex",gap:e*.08,marginTop:t*.04},children:[(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",gap:2},children:[(0,d.jsx)(O,{w:20,h:3,strong:!0}),(0,d.jsx)(O,{w:28,h:2})]}),(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",gap:2},children:[(0,d.jsx)(O,{w:20,h:3,strong:!0}),(0,d.jsx)(O,{w:28,h:2})]}),(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",gap:2},children:[(0,d.jsx)(O,{w:20,h:3,strong:!0}),(0,d.jsx)(O,{w:28,h:2})]})]})]})}function I5({width:e,height:t}){let n=Math.max(e*.6,80),o=Math.max(3,Math.floor(t/40));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex"},children:[(0,d.jsx)("div",{style:{width:e-n,background:"var(--agd-fill)",opacity:.3}}),(0,d.jsxs)("div",{style:{flex:1,borderLeft:"1px solid var(--agd-stroke)",display:"flex",flexDirection:"column",padding:e*.04},children:[(0,d.jsxs)("div",{style:{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:t*.06},children:[(0,d.jsx)(O,{w:n*.4,h:4,strong:!0}),(0,d.jsx)("div",{style:{width:12,height:12,border:"1px solid var(--agd-stroke)",borderRadius:3}})]}),Array.from({length:o},(r,l)=>(0,d.jsx)("div",{style:{padding:"6px 0"},children:(0,d.jsx)(O,{w:`${50+l*17%35}%`,h:2,strong:l===0})},l))]})]})}function N5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center"},children:[(0,d.jsxs)("div",{style:{flex:1,width:"100%",borderRadius:8,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",padding:10,display:"flex",flexDirection:"column",gap:5},children:[(0,d.jsx)(O,{w:"70%",h:3,strong:!0}),(0,d.jsx)(O,{w:"90%",h:2}),(0,d.jsx)(O,{w:"60%",h:2})]}),(0,d.jsx)("div",{style:{width:10,height:10,background:"var(--agd-fill)",border:"1px dashed var(--agd-stroke)",borderTop:"none",borderLeft:"none",transform:"rotate(45deg)",marginTop:-6}})]})}function $5({width:e,height:t}){let n=Math.min(t*.7,e*.3);return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",alignItems:"center",gap:e*.08},children:[(0,d.jsx)(it,{w:n,h:n,radius:n*.25}),(0,d.jsx)(O,{w:e*.45,h:Math.max(4,t*.2),strong:!0})]})}function R5({width:e,height:t}){let n=Math.max(2,Math.min(5,Math.floor(t/56)));return(0,d.jsx)("div",{style:{display:"flex",flexDirection:"column",height:"100%"},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{borderBottom:"1px solid var(--agd-stroke)",padding:"8px 6px",display:"flex",alignItems:"center",justifyContent:"space-between",flex:r===0?2:1},children:[(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:6},children:[(0,d.jsx)("span",{style:{fontSize:9,fontWeight:700,color:"var(--agd-stroke)"},children:"Q"}),(0,d.jsx)(O,{w:e*(.3+r*13%25/100),h:3,strong:!0})]}),(0,d.jsx)("span",{style:{fontSize:8,color:"var(--agd-stroke)"},children:r===0?"\u25BC":"\u25B6"})]},r))})}function P5({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/120))),o=Math.max(1,Math.min(3,Math.floor(t/120)));return(0,d.jsx)("div",{style:{display:"grid",gridTemplateColumns:`repeat(${n}, 1fr)`,gridTemplateRows:`repeat(${o}, 1fr)`,gap:4,height:"100%"},children:Array.from({length:n*o},(r,l)=>(0,d.jsx)("div",{style:{borderRadius:4,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",position:"relative",overflow:"hidden"},children:(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:"0 0 100 100",preserveAspectRatio:"none",fill:"none",children:[(0,d.jsx)("line",{x1:"0",y1:"0",x2:"100",y2:"100",stroke:"var(--agd-stroke)",strokeWidth:"0.5"}),(0,d.jsx)("line",{x1:"100",y1:"0",x2:"0",y2:"100",stroke:"var(--agd-stroke)",strokeWidth:"0.5"})]})},l))})}function T5({width:e,height:t}){let n=Math.min(e,t);return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("rect",{x:"1",y:(t-n+2)/2,width:n-2,height:n-2,rx:n*.15,stroke:"var(--agd-stroke)",strokeWidth:"1.5"}),(0,d.jsx)("path",{d:`M${n*.25} ${t/2}l${n*.2} ${n*.2} ${n*.3}-${n*.35}`,stroke:"var(--agd-bar)",strokeWidth:"1.5",fill:"none",strokeLinecap:"round",strokeLinejoin:"round"})]})}function D5({width:e,height:t}){let n=Math.min(e,t)/2-1;return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("circle",{cx:e/2,cy:t/2,r:n,stroke:"var(--agd-stroke)",strokeWidth:"1.5"}),(0,d.jsx)("circle",{cx:e/2,cy:t/2,r:n*.45,fill:"var(--agd-bar)"})]})}function B5({width:e,height:t}){let n=Math.max(2,t*.12),o=Math.min(t*.35,10),r=e*.55;return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",alignItems:"center",position:"relative"},children:[(0,d.jsx)("div",{style:{width:"100%",height:n,borderRadius:n/2,background:"var(--agd-fill)",border:"1px solid var(--agd-stroke)",position:"relative"},children:(0,d.jsx)("div",{style:{width:r,height:"100%",borderRadius:n/2,background:"var(--agd-bar)"}})}),(0,d.jsx)("div",{style:{position:"absolute",left:r-o,width:o*2,height:o*2,borderRadius:"50%",border:"1.5px solid var(--agd-stroke)",background:"var(--agd-fill)"}})]})}function z5({width:e,height:t}){let n=Math.min(36,t*.15),o=7,r=4,l=Math.min((e-16)/o,(t-n-40)/(r+1));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsxs)("div",{style:{height:n,borderRadius:4,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:"0 8px",justifyContent:"space-between"},children:[(0,d.jsx)(O,{w:"40%",h:2}),(0,d.jsxs)("svg",{width:"12",height:"12",viewBox:"0 0 16 16",fill:"none",children:[(0,d.jsx)("rect",{x:"2",y:"3",width:"12",height:"11",rx:"1",stroke:"var(--agd-stroke)",strokeWidth:"1"}),(0,d.jsx)("line",{x1:"2",y1:"6",x2:"14",y2:"6",stroke:"var(--agd-stroke)",strokeWidth:"0.5"})]})]}),(0,d.jsxs)("div",{style:{flex:1,borderRadius:6,border:"1px dashed var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",flexDirection:"column"},children:[(0,d.jsxs)("div",{style:{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"4px 6px"},children:[(0,d.jsx)("span",{style:{fontSize:7,color:"var(--agd-stroke)"},children:"\u2039"}),(0,d.jsx)(O,{w:e*.25,h:2,strong:!0}),(0,d.jsx)("span",{style:{fontSize:7,color:"var(--agd-stroke)"},children:"\u203A"})]}),(0,d.jsx)("div",{style:{display:"grid",gridTemplateColumns:`repeat(${o}, 1fr)`,gap:1,padding:"0 4px",flex:1},children:Array.from({length:o*r},(i,s)=>(0,d.jsx)("div",{style:{display:"flex",alignItems:"center",justifyContent:"center",height:l},children:(0,d.jsx)("div",{style:{width:l*.5,height:l*.5,borderRadius:"50%",background:s===10?"var(--agd-bar)":"transparent"},children:(0,d.jsx)("div",{style:{width:"100%",height:"100%",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)("div",{style:{width:1.5,height:1.5,borderRadius:1,background:"var(--agd-bar-strong)",opacity:s===10?1:.25}})})})},s))})]})]})}function O5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",gap:t*.08,padding:4},children:[(0,d.jsx)("div",{style:{width:"100%",height:t*.2,borderRadius:4,background:"var(--agd-fill)"}}),(0,d.jsx)("div",{style:{width:"70%",height:Math.max(6,t*.1),borderRadius:3,background:"var(--agd-fill)"}}),(0,d.jsx)("div",{style:{width:"90%",height:Math.max(4,t*.06),borderRadius:3,background:"var(--agd-fill)"}}),(0,d.jsx)("div",{style:{width:"50%",height:Math.max(4,t*.06),borderRadius:3,background:"var(--agd-fill)"}})]})}function A5({width:e,height:t}){return(0,d.jsx)("div",{style:{height:"100%",display:"flex",alignItems:"center",gap:6},children:(0,d.jsxs)("div",{style:{height:"100%",flex:1,borderRadius:t/2,border:"1px solid var(--agd-stroke)",background:"var(--agd-fill)",display:"flex",alignItems:"center",padding:`0 ${t*.3}px`,gap:4},children:[(0,d.jsx)(O,{w:"60%",h:2,strong:!0}),(0,d.jsx)("div",{style:{width:Math.max(6,t*.3),height:Math.max(6,t*.3),borderRadius:"50%",border:"1px solid var(--agd-stroke)",flexShrink:0,marginLeft:"auto"}})]})})}function W5({width:e,height:t}){let n=Math.min(e,t);return(0,d.jsx)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:(0,d.jsx)("path",{d:`M${e/2} ${(t-n)/2+n*.1}l${n*.12} ${n*.25} ${n*.28} ${n*.04}-${n*.2} ${n*.2} ${n*.05} ${n*.28}-${n*.25}-${n*.12}-${n*.25} ${n*.12} ${n*.05}-${n*.28}-${n*.2}-${n*.2} ${n*.28}-${n*.04}z`,stroke:"var(--agd-stroke)",strokeWidth:"1",fill:"var(--agd-fill)"})})}function F5({width:e,height:t}){let n=Math.min(e,t)/2-2;return(0,d.jsxs)("svg",{width:"100%",height:"100%",viewBox:`0 0 ${e} ${t}`,fill:"none",children:[(0,d.jsx)("circle",{cx:e/2,cy:t/2,r:n,stroke:"var(--agd-stroke)",strokeWidth:"1.5",opacity:".2"}),(0,d.jsx)("path",{d:`M${e/2} ${t/2-n}a${n} ${n} 0 0 1 ${n} ${n}`,stroke:"var(--agd-bar-strong)",strokeWidth:"1.5",strokeLinecap:"round"})]})}function j5({width:e,height:t}){let n=Math.min(36,t*.25,e*.12),o=Math.max(1,Math.min(3,Math.floor(t/80)));return(0,d.jsx)("div",{style:{display:"flex",flexDirection:"column",height:"100%",justifyContent:"space-around",padding:8},children:Array.from({length:o},(r,l)=>(0,d.jsxs)("div",{style:{display:"flex",gap:e*.04,alignItems:"flex-start"},children:[(0,d.jsx)(it,{w:n,h:n,radius:n*.25}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:4},children:[(0,d.jsx)(O,{w:`${40+l*13%20}%`,h:3,strong:!0}),(0,d.jsx)(O,{w:`${60+l*17%25}%`,h:2})]})]},l))})}function H5({width:e,height:t}){let n=Math.max(2,Math.min(4,Math.floor(e/120))),o=Math.min(36,t*.25);return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center",gap:t*.06,padding:t*.06},children:[(0,d.jsx)(O,{w:e*.3,h:4,strong:!0}),(0,d.jsx)("div",{style:{display:"flex",gap:e*.06,justifyContent:"center",flex:1,alignItems:"center"},children:Array.from({length:n},(r,l)=>(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",alignItems:"center",gap:6},children:[(0,d.jsx)(an,{size:o}),(0,d.jsx)(O,{w:e*.12,h:3,strong:!0}),(0,d.jsx)(O,{w:e*.08,h:2})]},l))})]})}function U5({width:e,height:t}){let n=Math.max(2,Math.min(3,Math.floor(t/80)));return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",alignItems:"center",padding:e*.06,gap:t*.04},children:[(0,d.jsx)(O,{w:e*.5,h:Math.max(5,t*.04),strong:!0}),(0,d.jsx)(O,{w:e*.35,h:2}),(0,d.jsx)("div",{style:{width:"100%",display:"flex",flexDirection:"column",gap:t*.03,marginTop:t*.04},children:Array.from({length:n},(o,r)=>(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:Math.min(60,e*.2),h:2}),(0,d.jsx)(it,{w:"100%",h:Math.min(32,t*.1),radius:4})]},r))}),(0,d.jsx)(it,{w:"100%",h:Math.min(36,t*.12),radius:6,style:{marginTop:t*.03,background:"var(--agd-bar)"}}),(0,d.jsx)(O,{w:e*.4,h:2})]})}function Y5({width:e,height:t}){return(0,d.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",padding:e*.04,gap:t*.03},children:[(0,d.jsx)(O,{w:e*.4,h:4,strong:!0}),(0,d.jsx)(O,{w:e*.6,h:2}),(0,d.jsxs)("div",{style:{display:"flex",gap:6,marginTop:t*.03},children:[(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:50,h:2}),(0,d.jsx)(it,{w:"100%",h:Math.min(28,t*.1),radius:4})]}),(0,d.jsxs)("div",{style:{flex:1,display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:40,h:2}),(0,d.jsx)(it,{w:"100%",h:Math.min(28,t*.1),radius:4})]})]}),(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:3},children:[(0,d.jsx)(O,{w:50,h:2}),(0,d.jsx)(it,{w:"100%",h:Math.min(28,t*.1),radius:4})]}),(0,d.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:3,flex:1},children:[(0,d.jsx)(O,{w:60,h:2}),(0,d.jsx)(it,{w:"100%",h:"100%",radius:4})]}),(0,d.jsx)(it,{w:Math.min(120,e*.3),h:Math.min(30,t*.1),radius:6,style:{alignSelf:"flex-end",background:"var(--agd-bar)"}})]})}var X5={navigation:Ty,hero:Dy,sidebar:By,footer:zy,modal:Oy,card:Ay,text:Wy,image:Fy,table:jy,list:Hy,button:Uy,input:Yy,form:Xy,tabs:Qy,avatar:Vy,badge:Ky,header:qy,section:Gy,grid:Zy,dropdown:Jy,toggle:e5,search:t5,toast:n5,progress:o5,chart:r5,video:l5,tooltip:i5,breadcrumb:s5,pagination:a5,divider:c5,accordion:d5,carousel:u5,pricing:_5,testimonial:f5,cta:h5,alert:p5,banner:m5,stat:g5,stepper:y5,tag:x5,rating:v5,map:w5,timeline:b5,fileUpload:k5,codeBlock:C5,calendar:S5,notification:M5,productCard:E5,profile:L5,drawer:I5,popover:N5,logo:$5,faq:R5,gallery:P5,checkbox:T5,radio:D5,slider:B5,datePicker:z5,skeleton:O5,chip:A5,icon:W5,spinner:F5,feature:j5,team:H5,login:U5,contact:Y5};function Q5({type:e,width:t,height:n,text:o}){let r=X5[e];return r?(0,d.jsx)("div",{style:{width:"100%",height:"100%",padding:8,position:"relative",pointerEvents:"none"},children:(0,d.jsx)(r,{width:t,height:n,text:o})}):(0,d.jsx)("div",{style:{width:"100%",height:"100%",display:"flex",alignItems:"center",justifyContent:"center"},children:(0,d.jsx)("span",{style:{fontSize:10,fontWeight:600,color:"var(--agd-text-3)",textTransform:"uppercase",letterSpacing:"0.06em",opacity:.5},children:e})})}var V5=`svg[fill=none] {
  fill: none !important;
}

.styles-module__overlayExiting___iEmYr {
  opacity: 0 !important;
  transition: opacity 0.25s ease !important;
  pointer-events: none !important;
}

.styles-module__overlay___aWh-q {
  position: fixed;
  inset: 0;
  z-index: 99995;
  pointer-events: auto;
  cursor: default;
  animation: styles-module__overlayFadeIn___aECVy 0.15s ease;
  --agd-stroke: rgba(59, 130, 246, 0.35);
  --agd-fill: rgba(59, 130, 246, 0.06);
  --agd-bar: rgba(59, 130, 246, 0.18);
  --agd-bar-strong: rgba(59, 130, 246, 0.28);
  --agd-text-3: rgba(255, 255, 255, 0.6);
  --agd-surface: #fff;
}
.styles-module__overlay___aWh-q.styles-module__light___ORIft {
  --agd-surface: #fff;
}
.styles-module__overlay___aWh-q:not(.styles-module__light___ORIft) {
  --agd-surface: #141414;
}
.styles-module__overlay___aWh-q.styles-module__wireframe___itvQU {
  --agd-stroke: rgba(249, 115, 22, 0.35);
  --agd-fill: rgba(249, 115, 22, 0.06);
  --agd-bar: rgba(249, 115, 22, 0.18);
  --agd-bar-strong: rgba(249, 115, 22, 0.28);
}
.styles-module__overlay___aWh-q.styles-module__placing___45yD8 {
  cursor: crosshair;
}
.styles-module__overlay___aWh-q.styles-module__passthrough___xaFeE {
  pointer-events: none;
}

.styles-module__blankCanvas___t2Eue {
  position: fixed;
  inset: 0;
  z-index: 99994;
  background: #fff;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}
.styles-module__blankCanvas___t2Eue.styles-module__visible___OKKqX {
  opacity: var(--canvas-opacity, 1);
  pointer-events: auto;
}
.styles-module__blankCanvas___t2Eue::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(0, 0, 0, 0.08) 1px, transparent 1px);
  background-size: 24px 24px;
  background-position: 12px 12px;
  pointer-events: none;
  transition: opacity 0.2s ease;
}
.styles-module__blankCanvas___t2Eue.styles-module__gridActive___OZ-cf::after {
  opacity: 1;
  background-image: radial-gradient(circle, rgba(0, 0, 0, 0.22) 1px, transparent 1px);
}

.styles-module__paletteHeader___-Q5gQ {
  padding: 0 1rem 0.375rem;
}

.styles-module__paletteHeaderTitle___oHqZC {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #fff;
  letter-spacing: -0.0094em;
}
.styles-module__light___ORIft .styles-module__paletteHeaderTitle___oHqZC {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__paletteHeaderDesc___6i74T {
  font-size: 0.6875rem;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
  line-height: 14px;
}
.styles-module__light___ORIft .styles-module__paletteHeaderDesc___6i74T {
  color: rgba(0, 0, 0, 0.45);
}
.styles-module__paletteHeaderDesc___6i74T a {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: underline dotted;
  text-decoration-color: rgba(255, 255, 255, 0.2);
  text-underline-offset: 2px;
  transition: color 0.15s ease;
}
.styles-module__paletteHeaderDesc___6i74T a:hover {
  color: #fff;
}
.styles-module__light___ORIft .styles-module__paletteHeaderDesc___6i74T a {
  color: rgba(0, 0, 0, 0.6);
  text-decoration-color: rgba(0, 0, 0, 0.2);
}
.styles-module__light___ORIft .styles-module__paletteHeaderDesc___6i74T a:hover {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__wireframePurposeWrap___To-tS {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.2s ease, opacity 0.15s ease;
  opacity: 1;
}
.styles-module__wireframePurposeWrap___To-tS.styles-module__collapsed___Ms9vS {
  grid-template-rows: 0fr;
  opacity: 0;
}

.styles-module__wireframePurposeInner___Lrahs {
  overflow: hidden;
}

.styles-module__wireframePurposeInput___7EtBN {
  display: block;
  width: calc(100% - 2rem);
  margin: 0.25rem 1rem 0.375rem;
  padding: 0.375rem 0.5rem;
  font-size: 0.8125rem;
  font-family: inherit;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.375rem;
  resize: none;
  outline: none;
  transition: border-color 0.15s ease;
  letter-spacing: -0.0094em;
}
.styles-module__wireframePurposeInput___7EtBN::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
.styles-module__wireframePurposeInput___7EtBN:focus {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
}
.styles-module__light___ORIft .styles-module__wireframePurposeInput___7EtBN {
  color: rgba(0, 0, 0, 0.7);
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.1);
}
.styles-module__light___ORIft .styles-module__wireframePurposeInput___7EtBN::placeholder {
  color: rgba(0, 0, 0, 0.3);
}
.styles-module__light___ORIft .styles-module__wireframePurposeInput___7EtBN:focus {
  border-color: rgba(0, 0, 0, 0.25);
  background: rgba(0, 0, 0, 0.05);
}

.styles-module__canvasToggle___-QqSy {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  margin: 0.25rem 1rem 0.25rem;
  padding: 0.375rem 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  background: transparent;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.styles-module__canvasToggle___-QqSy:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.15);
}
.styles-module__canvasToggle___-QqSy.styles-module__active___hosp7 {
  background: #f97316;
  border-color: transparent;
  border-style: solid;
  box-shadow: none;
}
.styles-module__light___ORIft .styles-module__canvasToggle___-QqSy {
  border-color: rgba(0, 0, 0, 0.08);
}
.styles-module__light___ORIft .styles-module__canvasToggle___-QqSy:hover {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.12);
}
.styles-module__light___ORIft .styles-module__canvasToggle___-QqSy.styles-module__active___hosp7 {
  background: #f97316;
  border-color: transparent;
  border-style: solid;
  box-shadow: none;
}

.styles-module__canvasToggleIcon___7pJ82 {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.35);
}
.styles-module__active___hosp7 .styles-module__canvasToggleIcon___7pJ82 {
  color: rgba(255, 255, 255, 0.85);
}
.styles-module__light___ORIft .styles-module__canvasToggleIcon___7pJ82 {
  color: rgba(0, 0, 0, 0.25);
}
.styles-module__light___ORIft .styles-module__active___hosp7 .styles-module__canvasToggleIcon___7pJ82 {
  color: rgba(255, 255, 255, 0.85);
}

.styles-module__canvasToggleLabel___OanpY {
  font-size: 0.8125rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: -0.0094em;
}
.styles-module__active___hosp7 .styles-module__canvasToggleLabel___OanpY {
  color: #fff;
}
.styles-module__light___ORIft .styles-module__canvasToggleLabel___OanpY {
  color: rgba(0, 0, 0, 0.5);
}
.styles-module__light___ORIft .styles-module__active___hosp7 .styles-module__canvasToggleLabel___OanpY {
  color: #fff;
}

.styles-module__canvasPurposeWrap___hj6zk {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.2s ease, opacity 0.15s ease;
  opacity: 1;
}
.styles-module__canvasPurposeWrap___hj6zk.styles-module__collapsed___Ms9vS {
  grid-template-rows: 0fr;
  opacity: 0;
}

.styles-module__canvasPurposeInner___VWiyu {
  overflow: hidden;
}

.styles-module__canvasPurposeToggle___byDH2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  margin: 0.375rem 1rem 0.375rem 1.1875rem;
}
.styles-module__canvasPurposeToggle___byDH2 input[type=checkbox] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.styles-module__canvasPurposeCheck___xqd7l {
  position: relative;
  width: 14px;
  height: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.25s ease, border-color 0.25s ease;
}
.styles-module__canvasPurposeCheck___xqd7l svg {
  color: #1a1a1a;
  opacity: 1;
  transition: opacity 0.15s ease;
}
.styles-module__canvasPurposeCheck___xqd7l.styles-module__checked___-1JGH {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgb(255, 255, 255);
}
.styles-module__light___ORIft .styles-module__canvasPurposeCheck___xqd7l {
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: #fff;
}
.styles-module__light___ORIft .styles-module__canvasPurposeCheck___xqd7l.styles-module__checked___-1JGH {
  border-color: #1a1a1a;
  background: #1a1a1a;
}
.styles-module__light___ORIft .styles-module__canvasPurposeCheck___xqd7l.styles-module__checked___-1JGH svg {
  color: #fff;
}

.styles-module__canvasPurposeLabel___Zu-tD {
  font-size: 0.8125rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: -0.0094em;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.styles-module__light___ORIft .styles-module__canvasPurposeLabel___Zu-tD {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__canvasPurposeHelp___jijwR {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: help;
}
.styles-module__canvasPurposeHelp___jijwR svg {
  color: rgba(255, 255, 255, 0.2);
  transform: translateY(2px);
  transition: color 0.15s ease;
}
.styles-module__canvasPurposeHelp___jijwR:hover svg {
  color: rgba(255, 255, 255, 0.5);
}
.styles-module__light___ORIft .styles-module__canvasPurposeHelp___jijwR svg {
  color: rgba(0, 0, 0, 0.2);
}
.styles-module__light___ORIft .styles-module__canvasPurposeHelp___jijwR:hover svg {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__placement___zcxv8 {
  position: absolute;
  border: 1.5px dashed rgba(59, 130, 246, 0.4);
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.08);
  cursor: grab;
  transition: box-shadow 0.15s, border-color 0.15s, opacity 0.15s ease, transform 0.15s ease;
  user-select: none;
  pointer-events: auto;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  animation: styles-module__placementEnter___TdRhf 0.25s cubic-bezier(0.34, 1.2, 0.64, 1);
}
.styles-module__placement___zcxv8:active {
  cursor: grabbing;
}
.styles-module__placement___zcxv8:hover {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12);
}
.styles-module__placement___zcxv8.styles-module__selected___6yrp6 {
  border-color: #3c82f7;
  border-style: solid;
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.15);
}
.styles-module__placement___zcxv8.styles-module__selected___6yrp6:hover {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.15);
}
.styles-module__wireframe___itvQU .styles-module__placement___zcxv8 {
  border-color: rgba(249, 115, 22, 0.4);
  background: rgba(249, 115, 22, 0.08);
}
.styles-module__wireframe___itvQU .styles-module__placement___zcxv8:hover {
  border-color: rgba(249, 115, 22, 0.5);
  background: rgba(249, 115, 22, 0.1);
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.12);
}
.styles-module__wireframe___itvQU .styles-module__placement___zcxv8.styles-module__selected___6yrp6 {
  border-color: #f97316;
  background: rgba(249, 115, 22, 0.1);
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.15), 0 2px 8px rgba(249, 115, 22, 0.15);
}
.styles-module__wireframe___itvQU .styles-module__placement___zcxv8.styles-module__selected___6yrp6:hover {
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.15), 0 2px 8px rgba(249, 115, 22, 0.15);
}
.styles-module__placement___zcxv8.styles-module__dragging___le6KZ {
  opacity: 0.85;
  z-index: 50;
}
.styles-module__placement___zcxv8.styles-module__exiting___YrM8F {
  opacity: 0;
  transform: scale(0.97);
  pointer-events: none;
  animation: none;
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.styles-module__placementContent___f64A4 {
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.styles-module__placementLabel___0KvWl {
  position: absolute;
  top: -18px;
  left: 0;
  font-size: 10px;
  font-weight: 600;
  color: rgba(59, 130, 246, 0.7);
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.8), 0 0 8px rgba(255, 255, 255, 0.5);
}
.styles-module__selected___6yrp6 .styles-module__placementLabel___0KvWl {
  color: #3c82f7;
}
.styles-module__wireframe___itvQU .styles-module__placementLabel___0KvWl {
  color: rgba(249, 115, 22, 0.7);
}
.styles-module__wireframe___itvQU .styles-module__selected___6yrp6 .styles-module__placementLabel___0KvWl {
  color: #f97316;
}

.styles-module__placementAnnotation___78pTr {
  position: absolute;
  bottom: -18px;
  left: 0;
  right: 0;
  font-weight: 450;
  color: rgba(0, 0, 0, 0.5);
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.9), 0 0 8px rgba(255, 255, 255, 0.6);
  opacity: 0;
  transform: translateY(-2px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.styles-module__placementAnnotation___78pTr.styles-module__annotationVisible___mrUyA {
  opacity: 1;
  transform: translateY(0);
}

.styles-module__sectionAnnotation___aUIs0 {
  position: absolute;
  bottom: -18px;
  left: 0;
  right: 0;
  font-weight: 450;
  color: rgba(59, 130, 246, 0.6);
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.9), 0 0 8px rgba(255, 255, 255, 0.6);
  opacity: 0;
  transform: translateY(-2px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.styles-module__sectionAnnotation___aUIs0.styles-module__annotationVisible___mrUyA {
  opacity: 1;
  transform: translateY(0);
}

.styles-module__handle___Ikbxm {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #fff;
  border: 1.5px solid #3c82f7;
  border-radius: 2px;
  z-index: 12;
  box-shadow: 0 0 0 0.5px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.12);
  opacity: 0;
  transform: scale(0.3);
  pointer-events: none;
  will-change: opacity, transform;
  transition: opacity 0.2s ease-out, transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.styles-module__placement___zcxv8:hover .styles-module__handle___Ikbxm, .styles-module__sectionOutline___s0hy-:hover .styles-module__handle___Ikbxm, .styles-module__ghostOutline___po-kO:hover .styles-module__handle___Ikbxm, .styles-module__placement___zcxv8:active .styles-module__handle___Ikbxm, .styles-module__sectionOutline___s0hy-:active .styles-module__handle___Ikbxm, .styles-module__ghostOutline___po-kO:active .styles-module__handle___Ikbxm, .styles-module__selected___6yrp6 .styles-module__handle___Ikbxm {
  opacity: 1;
  transform: scale(1);
  pointer-events: auto;
}
.styles-module__sectionOutline___s0hy- .styles-module__handle___Ikbxm {
  border-color: inherit;
}
.styles-module__wireframe___itvQU .styles-module__handle___Ikbxm {
  border-color: #f97316;
}

.styles-module__handleNw___4TMIj {
  top: -4px;
  left: -4px;
  cursor: nw-resize;
}

.styles-module__handleNe___mnsTh {
  top: -4px;
  right: -4px;
  cursor: ne-resize;
}

.styles-module__handleSe___oSFnk {
  bottom: -4px;
  right: -4px;
  cursor: se-resize;
}

.styles-module__handleSw___pi--Z {
  bottom: -4px;
  left: -4px;
  cursor: sw-resize;
}

.styles-module__handleN___aBA-Q, .styles-module__handleE___0hM5u, .styles-module__handleS___JjDRv, .styles-module__handleW___ERWGQ {
  opacity: 0 !important;
  pointer-events: none !important;
}

.styles-module__edgeHandle___XxXdT {
  position: absolute;
  z-index: 11;
  display: flex;
  align-items: center;
  justify-content: center;
}
.styles-module__edgeHandle___XxXdT::after {
  content: "";
  position: absolute;
  border-radius: 4px;
  background: #3c82f7;
}
.styles-module__wireframe___itvQU .styles-module__edgeHandle___XxXdT::after {
  background: #f97316;
}
.styles-module__edgeHandle___XxXdT::after {
  opacity: 0;
  transition: opacity 0.1s ease, transform 0.1s ease;
  transform: scale(0.8);
}
.styles-module__edgeHandle___XxXdT:hover::after {
  opacity: 0.85;
  transform: scale(1);
}
.styles-module__edgeHandle___XxXdT svg {
  position: relative;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.1s ease;
  filter: drop-shadow(0 0 2px var(--agd-surface));
}
.styles-module__edgeHandle___XxXdT:hover svg {
  opacity: 1;
}

.styles-module__edgeN___-JJDj, .styles-module__edgeS___66lMX {
  left: 12px;
  right: 12px;
  height: 12px;
  cursor: n-resize;
}
.styles-module__edgeN___-JJDj::after, .styles-module__edgeS___66lMX::after {
  width: 24px;
  height: 4px;
}

.styles-module__edgeN___-JJDj {
  top: -6px;
}

.styles-module__edgeS___66lMX {
  bottom: -6px;
  cursor: s-resize;
}

.styles-module__edgeE___1bGDa, .styles-module__edgeW___lHQNo {
  top: 12px;
  bottom: 12px;
  width: 12px;
  cursor: e-resize;
}
.styles-module__edgeE___1bGDa::after, .styles-module__edgeW___lHQNo::after {
  width: 4px;
  height: 24px;
}

.styles-module__edgeE___1bGDa {
  right: -6px;
}

.styles-module__edgeW___lHQNo {
  left: -6px;
  cursor: w-resize;
}

.styles-module__deleteButton___LkGCb {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.35);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  z-index: 15;
  pointer-events: none;
  opacity: 0;
  transform: scale(0.8);
  will-change: opacity, transform;
  transition: opacity 0.2s ease-out, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.12s ease, color 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
}
.styles-module__placement___zcxv8:hover .styles-module__deleteButton___LkGCb, .styles-module__selected___6yrp6 .styles-module__deleteButton___LkGCb, .styles-module__sectionOutline___s0hy-:hover .styles-module__deleteButton___LkGCb, .styles-module__sectionOutline___s0hy-.styles-module__selected___6yrp6 .styles-module__deleteButton___LkGCb, .styles-module__ghostOutline___po-kO:hover .styles-module__deleteButton___LkGCb, .styles-module__ghostOutline___po-kO.styles-module__selected___6yrp6 .styles-module__deleteButton___LkGCb {
  opacity: 1;
  transform: scale(1);
  pointer-events: auto;
}
.styles-module__deleteButton___LkGCb:hover {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
  box-shadow: 0 1px 4px rgba(239, 68, 68, 0.3);
  transform: scale(1.1);
}
.styles-module__overlay___aWh-q:not(.styles-module__light___ORIft) .styles-module__deleteButton___LkGCb, .styles-module__rearrangeOverlay___-3R3t:not(.styles-module__light___ORIft) .styles-module__deleteButton___LkGCb {
  background: rgba(40, 40, 40, 0.9);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
.styles-module__overlay___aWh-q:not(.styles-module__light___ORIft) .styles-module__deleteButton___LkGCb:hover, .styles-module__rearrangeOverlay___-3R3t:not(.styles-module__light___ORIft) .styles-module__deleteButton___LkGCb:hover {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
}

.styles-module__drawBox___BrVAa {
  position: fixed;
  pointer-events: none;
  z-index: 99996;
  border: 2px solid #3c82f7;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.15);
}

.styles-module__selectBox___Iu8kB {
  position: fixed;
  pointer-events: none;
  z-index: 99996;
  border: 1px dashed #3c82f7;
  background: rgba(59, 130, 246, 0.08);
  border-radius: 2px;
}

.styles-module__sizeIndicator___7zJ4y {
  position: fixed;
  pointer-events: none;
  z-index: 100001;
  font-size: 10px;
  color: #fff;
  background: #3c82f7;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.styles-module__guideLine___DUQY2 {
  pointer-events: none;
  z-index: 100001;
  background: #f0f;
  opacity: 0.5;
}

.styles-module__dragPreview___onPbU {
  position: fixed;
  z-index: 100002;
  pointer-events: none;
  border: 1.5px dashed #3c82f7;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.1);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 600;
  color: #3c82f7;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
  transition: width 0.08s ease, height 0.08s ease, opacity 0.08s ease;
}

.styles-module__dragPreviewWireframe___jsg0G {
  border-color: #f97316;
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.15);
}

.styles-module__palette___C7iSH {
  position: absolute;
  right: 5px;
  bottom: calc(100% + 0.5rem);
  width: 256px;
  overflow: hidden;
  background: #1c1c1c;
  border: none;
  border-radius: 1rem;
  padding: 13px 0 16px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.04);
  z-index: 100001;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  cursor: default;
  opacity: 0;
  filter: blur(5px);
}
.styles-module__palette___C7iSH .styles-module__paletteItem___6TlnA,
.styles-module__palette___C7iSH .styles-module__paletteItemLabel___6ncO4,
.styles-module__palette___C7iSH .styles-module__paletteSectionTitle___PqnjX,
.styles-module__palette___C7iSH .styles-module__paletteFooter___QYnAG {
  transition: background 0.25s ease, color 0.25s ease, border-color 0.25s ease;
}
.styles-module__palette___C7iSH.styles-module__enter___6LYk5 {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0px);
  transition: opacity 0.2s ease, transform 0.2s ease, filter 0.2s ease;
}
.styles-module__palette___C7iSH.styles-module__exit___iSGRw {
  opacity: 0;
  transform: translateY(6px);
  filter: blur(5px);
  pointer-events: none;
  transition: opacity 0.1s ease, transform 0.1s ease, filter 0.1s ease;
}
.styles-module__palette___C7iSH.styles-module__light___ORIft {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04);
}

.styles-module__paletteSection___V8DEA {
  padding: 0 1rem;
}
.styles-module__paletteSection___V8DEA + .styles-module__paletteSection___V8DEA {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}
.styles-module__light___ORIft .styles-module__paletteSection___V8DEA + .styles-module__paletteSection___V8DEA {
  border-top-color: rgba(0, 0, 0, 0.07);
}

.styles-module__paletteSectionTitle___PqnjX {
  font-size: 0.6875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: -0.0094em;
  padding: 0 0 3px 3px;
}
.styles-module__light___ORIft .styles-module__paletteSectionTitle___PqnjX {
  color: rgba(0, 0, 0, 0.4);
}

.styles-module__paletteItem___6TlnA {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.25rem;
  margin-bottom: 1px;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  border: 1px solid transparent;
  user-select: none;
  min-height: 24px;
}
.styles-module__paletteItem___6TlnA:hover {
  background: rgba(255, 255, 255, 0.1);
}
.styles-module__paletteItem___6TlnA.styles-module__active___hosp7 {
  background: #3c82f7;
  border-color: transparent;
}
.styles-module__paletteItem___6TlnA.styles-module__wireframe___itvQU.styles-module__active___hosp7 {
  background: #f97316;
}
.styles-module__light___ORIft .styles-module__paletteItem___6TlnA:hover {
  background: rgba(0, 0, 0, 0.05);
}
.styles-module__light___ORIft .styles-module__paletteItem___6TlnA.styles-module__active___hosp7 {
  background: #3c82f7;
  border-color: transparent;
}
.styles-module__light___ORIft .styles-module__paletteItem___6TlnA.styles-module__wireframe___itvQU.styles-module__active___hosp7 {
  background: #f97316;
}

.styles-module__paletteItemIcon___0NPQK {
  width: 20px;
  height: 16px;
  border-radius: 2px;
  border: 1px dashed rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.45);
}
.styles-module__paletteItemIcon___0NPQK svg {
  display: block;
  width: 20px;
  height: 16px;
}
.styles-module__active___hosp7 .styles-module__paletteItemIcon___0NPQK {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}
.styles-module__light___ORIft .styles-module__paletteItemIcon___0NPQK {
  border-color: rgba(0, 0, 0, 0.12);
  background: rgba(0, 0, 0, 0.02);
  color: rgba(0, 0, 0, 0.4);
}
.styles-module__light___ORIft .styles-module__active___hosp7 .styles-module__paletteItemIcon___0NPQK {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.styles-module__paletteItemLabel___6ncO4 {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: -0.0094em;
  line-height: 1;
  min-width: 0;
}
.styles-module__active___hosp7 .styles-module__paletteItemLabel___6ncO4 {
  color: #fff;
  font-weight: 600;
}
.styles-module__light___ORIft .styles-module__paletteItemLabel___6ncO4 {
  color: rgba(0, 0, 0, 0.7);
}
.styles-module__light___ORIft .styles-module__active___hosp7 .styles-module__paletteItemLabel___6ncO4 {
  color: #fff;
  font-weight: 600;
}

.styles-module__placeScroll___7sClM {
  max-height: 240px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 0.25rem;
}
.styles-module__placeScroll___7sClM.styles-module__fadeTop___KT9tF {
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, black 32px);
  mask-image: linear-gradient(to bottom, transparent 0, black 32px);
}
.styles-module__placeScroll___7sClM.styles-module__fadeBottom___x3ShT {
  -webkit-mask-image: linear-gradient(to bottom, black calc(100% - 32px), transparent 100%);
  mask-image: linear-gradient(to bottom, black calc(100% - 32px), transparent 100%);
}
.styles-module__placeScroll___7sClM.styles-module__fadeTop___KT9tF.styles-module__fadeBottom___x3ShT {
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, black 32px, black calc(100% - 32px), transparent 100%);
  mask-image: linear-gradient(to bottom, transparent 0, black 32px, black calc(100% - 32px), transparent 100%);
}
.styles-module__placeScroll___7sClM::-webkit-scrollbar {
  width: 3px;
}
.styles-module__placeScroll___7sClM::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
}
.styles-module__light___ORIft .styles-module__placeScroll___7sClM::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
}

.styles-module__paletteFooterWrap___71-fI {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.25s cubic-bezier(0.32, 0.72, 0, 1);
}
.styles-module__paletteFooterWrap___71-fI.styles-module__footerHidden___fJUik {
  grid-template-rows: 0fr;
}

.styles-module__paletteFooterInnerContent___VC26h {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.styles-module__footerHidden___fJUik .styles-module__paletteFooterInnerContent___VC26h {
  opacity: 0;
  transform: translateY(4px);
}

.styles-module__paletteFooterInner___dfylY {
  overflow: hidden;
}

.styles-module__paletteFooter___QYnAG {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
  padding: 0 1rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}
.styles-module__light___ORIft .styles-module__paletteFooter___QYnAG {
  border-top-color: rgba(0, 0, 0, 0.07);
}

.styles-module__paletteFooterCount___D3Fia {
  font-size: 0.8125rem;
  font-weight: 400;
  letter-spacing: -0.0094em;
  color: rgba(255, 255, 255, 0.5);
}
.styles-module__light___ORIft .styles-module__paletteFooterCount___D3Fia {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__paletteFooterClear___ybBoa {
  font-size: 0.8125rem;
  font-weight: 400;
  letter-spacing: -0.0094em;
  color: rgba(255, 255, 255, 0.5);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
  transition: color 0.15s ease;
}
.styles-module__paletteFooterClear___ybBoa:hover {
  color: rgba(255, 255, 255, 0.7);
}
.styles-module__light___ORIft .styles-module__paletteFooterClear___ybBoa {
  color: rgba(0, 0, 0, 0.5);
}
.styles-module__light___ORIft .styles-module__paletteFooterClear___ybBoa:hover {
  color: rgba(0, 0, 0, 0.6);
}

.styles-module__paletteFooterActions___fLzv8 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.styles-module__rollingWrap___S75jM {
  display: inline-block;
  overflow: hidden;
  height: 1.15em;
  position: relative;
  vertical-align: bottom;
}

.styles-module__rollingNum___1RKDx {
  position: absolute;
  left: 0;
  top: 0;
}

.styles-module__exitUp___AFDRW {
  animation: styles-module__numExitUp___FRQqx 0.25s cubic-bezier(0.32, 0.72, 0, 1) forwards;
}

.styles-module__enterUp___CPlXb {
  animation: styles-module__numEnterUp___2Yd-w 0.25s cubic-bezier(0.32, 0.72, 0, 1) forwards;
}

.styles-module__exitDown___-1yAy {
  animation: styles-module__numExitDown___xm5by 0.25s cubic-bezier(0.32, 0.72, 0, 1) forwards;
}

.styles-module__enterDown___DDuFR {
  animation: styles-module__numEnterDown___hpxBk 0.25s cubic-bezier(0.32, 0.72, 0, 1) forwards;
}

@keyframes styles-module__numExitUp___FRQqx {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-110%);
    opacity: 0;
  }
}
@keyframes styles-module__numEnterUp___2Yd-w {
  from {
    transform: translateY(110%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
@keyframes styles-module__numExitDown___xm5by {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(110%);
    opacity: 0;
  }
}
@keyframes styles-module__numEnterDown___hpxBk {
  from {
    transform: translateY(-110%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
.styles-module__rearrangeOverlay___-3R3t {
  position: fixed;
  inset: 0;
  z-index: 99995;
  pointer-events: none;
  cursor: default;
  user-select: none;
  animation: styles-module__overlayFadeIn___aECVy 0.15s ease;
}

.styles-module__hoverHighlight___8eT-v {
  position: fixed;
  pointer-events: none;
  z-index: 99994;
  border: 2px dashed rgba(59, 130, 246, 0.5);
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.06);
  animation: styles-module__highlightFadeIn___Lg7KY 0.12s ease;
}

.styles-module__sectionOutline___s0hy- {
  position: fixed;
  border: 2px solid;
  border-radius: 4px;
  cursor: grab;
}
.styles-module__sectionOutline___s0hy-:active {
  cursor: grabbing;
}
.styles-module__sectionOutline___s0hy- {
  transition: box-shadow 0.15s, border-color 0.3s, background-color 0.3s, border-style 0s;
  user-select: none;
  pointer-events: auto;
  animation: styles-module__sectionEnter___-8BXT 0.2s ease;
}
.styles-module__sectionOutline___s0hy-:hover {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 4px 12px rgba(0, 0, 0, 0.15);
}
.styles-module__sectionOutline___s0hy-.styles-module__selected___6yrp6 {
  border-style: solid;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.15);
}
.styles-module__sectionOutline___s0hy-.styles-module__selected___6yrp6:hover {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.15);
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6) {
  border: 1.5px dashed rgba(150, 150, 150, 0.35);
  background-color: transparent !important;
  box-shadow: none;
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6):hover {
  border-color: rgba(150, 150, 150, 0.6);
  box-shadow: none;
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6) .styles-module__sectionLabel___F80HQ {
  opacity: 0;
  transition: opacity 0.15s ease;
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6):hover .styles-module__sectionLabel___F80HQ {
  opacity: 1;
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6) .styles-module__movedBadge___s8z-q,
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6) .styles-module__sectionDimensions___RcJSL {
  opacity: 0;
  transition: opacity 0.15s ease;
}
.styles-module__sectionOutline___s0hy-.styles-module__settled___b5U5o:not(.styles-module__selected___6yrp6):hover .styles-module__sectionDimensions___RcJSL {
  opacity: 1;
}
.styles-module__sectionOutline___s0hy-.styles-module__exiting___YrM8F {
  opacity: 0;
  transform: scale(0.97);
  pointer-events: none;
  animation: none;
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.styles-module__sectionLabel___F80HQ {
  position: absolute;
  top: 4px;
  left: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  max-width: calc(100% - 8px);
  overflow: hidden;
  text-overflow: ellipsis;
}

.styles-module__movedBadge___s8z-q {
  position: absolute;
  bottom: 22px;
  right: 4px;
  font-size: 9px;
  font-weight: 700;
  color: #fff;
  background: #22c55e;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.styles-module__movedBadge___s8z-q.styles-module__badgeVisible___npbdS {
  opacity: 1;
  transform: scale(1);
  transition: opacity 0.2s cubic-bezier(0.34, 1.2, 0.64, 1), transform 0.2s cubic-bezier(0.34, 1.2, 0.64, 1);
}

.styles-module__resizedBadge___u51V8 {
  background: #3c82f7;
  bottom: 40px;
}

.styles-module__sectionDimensions___RcJSL {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 9px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 0, 0, 0.5);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.styles-module__light___ORIft .styles-module__sectionDimensions___RcJSL {
  color: rgba(0, 0, 0, 0.5);
  background: rgba(255, 255, 255, 0.7);
}

.styles-module__wireframeNotice___4GJyB {
  position: fixed;
  bottom: 16px;
  left: 24px;
  z-index: 99995;
  font-size: 9.5px;
  font-weight: 400;
  color: rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  pointer-events: auto;
  animation: styles-module__overlayFadeIn___aECVy 0.3s ease;
  line-height: 1.5;
  max-width: 280px;
}

.styles-module__wireframeOpacityRow___CJXzi {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.styles-module__wireframeOpacityLabel___afkfT {
  font-size: 9px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.32);
  letter-spacing: 0.02em;
  white-space: nowrap;
  user-select: none;
}

.styles-module__wireframeOpacitySlider___YcoEs {
  -webkit-appearance: none;
  appearance: none;
  width: 56px;
  height: 4px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.styles-module__wireframeOpacitySlider___YcoEs:hover {
  background: rgba(0, 0, 0, 0.13);
}
.styles-module__wireframeOpacitySlider___YcoEs::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f97316;
  cursor: pointer;
  transition: background 0.15s ease;
}
.styles-module__wireframeOpacitySlider___YcoEs::-webkit-slider-thumb:hover {
  background: rgb(224.4209205021, 95.3548117155, 5.7790794979);
}
.styles-module__wireframeOpacitySlider___YcoEs::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f97316;
  border: none;
  cursor: pointer;
}
.styles-module__wireframeOpacitySlider___YcoEs::-moz-range-track {
  background: rgba(0, 0, 0, 0.08);
  height: 4px;
  border-radius: 2px;
}

.styles-module__wireframeNoticeTitleRow___PJqyG {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 2px;
}

.styles-module__wireframeNoticeTitle___okr08 {
  font-weight: 600;
  color: rgba(0, 0, 0, 0.55);
}

.styles-module__wireframeNoticeDivider___PNKQ6 {
  width: 1px;
  height: 8px;
  background: rgba(0, 0, 0, 0.12);
  margin: 0 8px;
  flex-shrink: 0;
}

.styles-module__wireframeStartOver___YFk-I {
  font-size: 9.5px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.35);
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  font-family: inherit;
  text-decoration: none;
  transition: color 0.12s ease;
  white-space: nowrap;
}
.styles-module__wireframeStartOver___YFk-I:hover {
  color: rgba(0, 0, 0, 0.6);
}

.styles-module__ghostOutline___po-kO {
  position: fixed;
  border: 1.5px dashed rgba(59, 130, 246, 0.4);
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.04);
  cursor: grab;
  opacity: 0.5;
  user-select: none;
  pointer-events: auto;
  animation: styles-module__ghostEnter___EC3Mb 0.25s ease;
  transition: box-shadow 0.15s, border-color 0.3s, opacity 0.25s;
}
.styles-module__ghostOutline___po-kO:active {
  cursor: grabbing;
}
.styles-module__ghostOutline___po-kO:hover {
  opacity: 0.7;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1), 0 4px 12px rgba(0, 0, 0, 0.08);
}
.styles-module__ghostOutline___po-kO.styles-module__selected___6yrp6 {
  opacity: 1;
  border-style: solid;
  border-width: 2px;
  border-color: #3c82f7;
  background: rgba(59, 130, 246, 0.08);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.15);
}
.styles-module__ghostOutline___po-kO.styles-module__exiting___YrM8F {
  opacity: 0;
  transform: scale(0.97);
  pointer-events: none;
  animation: none;
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.styles-module__ghostBadge___tsQUK {
  position: absolute;
  bottom: calc(100% + 4px);
  left: -1px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(59, 130, 246, 0.9);
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  letter-spacing: 0.02em;
  line-height: 1.2;
  animation: styles-module__badgeSlideIn___typJ7 0.2s ease both;
}

@keyframes styles-module__badgeSlideIn___typJ7 {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.styles-module__ghostBadgeExtra___6CVoD {
  display: inline;
  animation: styles-module__badgeExtraIn___i4W8F 0.2s ease both;
}

@keyframes styles-module__badgeExtraIn___i4W8F {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.styles-module__originalOutline___Y6DD1 {
  position: fixed;
  border: 1.5px dashed rgba(150, 150, 150, 0.3);
  border-radius: 4px;
  background: transparent;
  pointer-events: none;
  user-select: none;
  animation: styles-module__sectionEnter___-8BXT 0.2s ease;
}

.styles-module__originalLabel___HqI9g {
  position: absolute;
  top: 4px;
  left: 4px;
  font-size: 9px;
  font-weight: 500;
  color: rgba(150, 150, 150, 0.5);
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: rgba(150, 150, 150, 0.08);
}

.styles-module__connectorSvg___Lovld {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 99996;
}

.styles-module__connectorLine___XeWh- {
  transition: opacity 0.2s ease;
  animation: styles-module__connectorDraw___8sK5I 0.3s ease both;
}

.styles-module__connectorDot___yvf7C {
  transform-box: fill-box;
  transform-origin: center;
  animation: styles-module__connectorDotIn___NwTUq 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) 0.15s both;
}

@keyframes styles-module__connectorDraw___8sK5I {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes styles-module__connectorDotIn___NwTUq {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
.styles-module__connectorExiting___2lLOs {
  animation: styles-module__connectorOut___5QoPl 0.2s ease forwards;
}
.styles-module__connectorExiting___2lLOs .styles-module__connectorDot___yvf7C {
  animation: styles-module__connectorDotOut___FEq7e 0.2s ease forwards;
}

@keyframes styles-module__connectorOut___5QoPl {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
@keyframes styles-module__connectorDotOut___FEq7e {
  from {
    transform: scale(1);
    opacity: 1;
  }
  to {
    transform: scale(0);
    opacity: 0;
  }
}
@keyframes styles-module__placementEnter___TdRhf {
  from {
    opacity: 0;
    transform: scale(0.85);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__sectionEnter___-8BXT {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__highlightFadeIn___Lg7KY {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes styles-module__overlayFadeIn___aECVy {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes styles-module__ghostEnter___EC3Mb {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 0.6;
    transform: scale(1);
  }
}`,K5={overlayExiting:"styles-module__overlayExiting___iEmYr",overlay:"styles-module__overlay___aWh-q",overlayFadeIn:"styles-module__overlayFadeIn___aECVy",light:"styles-module__light___ORIft",wireframe:"styles-module__wireframe___itvQU",placing:"styles-module__placing___45yD8",passthrough:"styles-module__passthrough___xaFeE",blankCanvas:"styles-module__blankCanvas___t2Eue",visible:"styles-module__visible___OKKqX",gridActive:"styles-module__gridActive___OZ-cf",paletteHeader:"styles-module__paletteHeader___-Q5gQ",paletteHeaderTitle:"styles-module__paletteHeaderTitle___oHqZC",paletteHeaderDesc:"styles-module__paletteHeaderDesc___6i74T",wireframePurposeWrap:"styles-module__wireframePurposeWrap___To-tS",collapsed:"styles-module__collapsed___Ms9vS",wireframePurposeInner:"styles-module__wireframePurposeInner___Lrahs",wireframePurposeInput:"styles-module__wireframePurposeInput___7EtBN",canvasToggle:"styles-module__canvasToggle___-QqSy",active:"styles-module__active___hosp7",canvasToggleIcon:"styles-module__canvasToggleIcon___7pJ82",canvasToggleLabel:"styles-module__canvasToggleLabel___OanpY",canvasPurposeWrap:"styles-module__canvasPurposeWrap___hj6zk",canvasPurposeInner:"styles-module__canvasPurposeInner___VWiyu",canvasPurposeToggle:"styles-module__canvasPurposeToggle___byDH2",canvasPurposeCheck:"styles-module__canvasPurposeCheck___xqd7l",checked:"styles-module__checked___-1JGH",canvasPurposeLabel:"styles-module__canvasPurposeLabel___Zu-tD",canvasPurposeHelp:"styles-module__canvasPurposeHelp___jijwR",placement:"styles-module__placement___zcxv8",placementEnter:"styles-module__placementEnter___TdRhf",selected:"styles-module__selected___6yrp6",dragging:"styles-module__dragging___le6KZ",exiting:"styles-module__exiting___YrM8F",placementContent:"styles-module__placementContent___f64A4",placementLabel:"styles-module__placementLabel___0KvWl",placementAnnotation:"styles-module__placementAnnotation___78pTr",annotationVisible:"styles-module__annotationVisible___mrUyA",sectionAnnotation:"styles-module__sectionAnnotation___aUIs0",handle:"styles-module__handle___Ikbxm",sectionOutline:"styles-module__sectionOutline___s0hy-",ghostOutline:"styles-module__ghostOutline___po-kO",handleNw:"styles-module__handleNw___4TMIj",handleNe:"styles-module__handleNe___mnsTh",handleSe:"styles-module__handleSe___oSFnk",handleSw:"styles-module__handleSw___pi--Z",handleN:"styles-module__handleN___aBA-Q",handleE:"styles-module__handleE___0hM5u",handleS:"styles-module__handleS___JjDRv",handleW:"styles-module__handleW___ERWGQ",edgeHandle:"styles-module__edgeHandle___XxXdT",edgeN:"styles-module__edgeN___-JJDj",edgeS:"styles-module__edgeS___66lMX",edgeE:"styles-module__edgeE___1bGDa",edgeW:"styles-module__edgeW___lHQNo",deleteButton:"styles-module__deleteButton___LkGCb",rearrangeOverlay:"styles-module__rearrangeOverlay___-3R3t",drawBox:"styles-module__drawBox___BrVAa",selectBox:"styles-module__selectBox___Iu8kB",sizeIndicator:"styles-module__sizeIndicator___7zJ4y",guideLine:"styles-module__guideLine___DUQY2",dragPreview:"styles-module__dragPreview___onPbU",dragPreviewWireframe:"styles-module__dragPreviewWireframe___jsg0G",palette:"styles-module__palette___C7iSH",paletteItem:"styles-module__paletteItem___6TlnA",paletteItemLabel:"styles-module__paletteItemLabel___6ncO4",paletteSectionTitle:"styles-module__paletteSectionTitle___PqnjX",paletteFooter:"styles-module__paletteFooter___QYnAG",enter:"styles-module__enter___6LYk5",exit:"styles-module__exit___iSGRw",paletteSection:"styles-module__paletteSection___V8DEA",paletteItemIcon:"styles-module__paletteItemIcon___0NPQK",placeScroll:"styles-module__placeScroll___7sClM",fadeTop:"styles-module__fadeTop___KT9tF",fadeBottom:"styles-module__fadeBottom___x3ShT",paletteFooterWrap:"styles-module__paletteFooterWrap___71-fI",footerHidden:"styles-module__footerHidden___fJUik",paletteFooterInnerContent:"styles-module__paletteFooterInnerContent___VC26h",paletteFooterInner:"styles-module__paletteFooterInner___dfylY",paletteFooterCount:"styles-module__paletteFooterCount___D3Fia",paletteFooterClear:"styles-module__paletteFooterClear___ybBoa",paletteFooterActions:"styles-module__paletteFooterActions___fLzv8",rollingWrap:"styles-module__rollingWrap___S75jM",rollingNum:"styles-module__rollingNum___1RKDx",exitUp:"styles-module__exitUp___AFDRW",numExitUp:"styles-module__numExitUp___FRQqx",enterUp:"styles-module__enterUp___CPlXb",numEnterUp:"styles-module__numEnterUp___2Yd-w",exitDown:"styles-module__exitDown___-1yAy",numExitDown:"styles-module__numExitDown___xm5by",enterDown:"styles-module__enterDown___DDuFR",numEnterDown:"styles-module__numEnterDown___hpxBk",hoverHighlight:"styles-module__hoverHighlight___8eT-v",highlightFadeIn:"styles-module__highlightFadeIn___Lg7KY",sectionEnter:"styles-module__sectionEnter___-8BXT",settled:"styles-module__settled___b5U5o",sectionLabel:"styles-module__sectionLabel___F80HQ",movedBadge:"styles-module__movedBadge___s8z-q",sectionDimensions:"styles-module__sectionDimensions___RcJSL",badgeVisible:"styles-module__badgeVisible___npbdS",resizedBadge:"styles-module__resizedBadge___u51V8",wireframeNotice:"styles-module__wireframeNotice___4GJyB",wireframeOpacityRow:"styles-module__wireframeOpacityRow___CJXzi",wireframeOpacityLabel:"styles-module__wireframeOpacityLabel___afkfT",wireframeOpacitySlider:"styles-module__wireframeOpacitySlider___YcoEs",wireframeNoticeTitleRow:"styles-module__wireframeNoticeTitleRow___PJqyG",wireframeNoticeTitle:"styles-module__wireframeNoticeTitle___okr08",wireframeNoticeDivider:"styles-module__wireframeNoticeDivider___PNKQ6",wireframeStartOver:"styles-module__wireframeStartOver___YFk-I",ghostEnter:"styles-module__ghostEnter___EC3Mb",ghostBadge:"styles-module__ghostBadge___tsQUK",badgeSlideIn:"styles-module__badgeSlideIn___typJ7",ghostBadgeExtra:"styles-module__ghostBadgeExtra___6CVoD",badgeExtraIn:"styles-module__badgeExtraIn___i4W8F",originalOutline:"styles-module__originalOutline___Y6DD1",originalLabel:"styles-module__originalLabel___HqI9g",connectorSvg:"styles-module__connectorSvg___Lovld",connectorLine:"styles-module__connectorLine___XeWh-",connectorDraw:"styles-module__connectorDraw___8sK5I",connectorDot:"styles-module__connectorDot___yvf7C",connectorDotIn:"styles-module__connectorDotIn___NwTUq",connectorExiting:"styles-module__connectorExiting___2lLOs",connectorOut:"styles-module__connectorOut___5QoPl",connectorDotOut:"styles-module__connectorDotOut___FEq7e"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-design-mode-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-design-mode-styles",document.head.appendChild(e)),e.textContent=V5}var T=K5,yl=24,wa=5;function Jh(e,t,n,o,r){let l=1/0,i=1/0,s=e.x,a=e.x+e.width,m=e.x+e.width/2,p=e.y,b=e.y+e.height,y=e.y+e.height/2,R=!o,C=R?[s,a,m]:[...o.left?[s]:[],...o.right?[a]:[]],N=R?[p,b,y]:[...o.top?[p]:[],...o.bottom?[b]:[]],L=[];for(let he of t)n.has(he.id)||L.push(he);r&&L.push(...r);for(let he of L){let Ge=he.x,st=he.x+he.width,Re=he.x+he.width/2,We=he.y,Ee=he.y+he.height,qe=he.y+he.height/2;for(let Q of C)for(let me of[Ge,st,Re]){let Ye=me-Q;Math.abs(Ye)<wa&&Math.abs(Ye)<Math.abs(l)&&(l=Ye)}for(let Q of N)for(let me of[We,Ee,qe]){let Ye=me-Q;Math.abs(Ye)<wa&&Math.abs(Ye)<Math.abs(i)&&(i=Ye)}}let f=Math.abs(l)<wa?l:0,g=Math.abs(i)<wa?i:0,w=[],$=new Set,U=s+f,V=a+f,B=m+f,q=p+g,ye=b+g,Z=y+g;for(let he of L){let Ge=he.x,st=he.x+he.width,Re=he.x+he.width/2,We=he.y,Ee=he.y+he.height,qe=he.y+he.height/2;for(let Q of[Ge,Re,st])for(let me of[U,B,V])if(Math.abs(me-Q)<.5){let Ye=`x:${Math.round(Q)}`;$.has(Ye)||($.add(Ye),w.push({axis:"x",pos:Q}))}for(let Q of[We,qe,Ee])for(let me of[q,Z,ye])if(Math.abs(me-Q)<.5){let Ye=`y:${Math.round(Q)}`;$.has(Ye)||($.add(Ye),w.push({axis:"y",pos:Q}))}}return{dx:f,dy:g,guides:w}}function ep(){return`dp-${Date.now()}-${Math.random().toString(36).slice(2,7)}`}function q5({placements:e,onChange:t,activeComponent:n,onActiveComponentChange:o,isDarkMode:r,exiting:l,onInteractionChange:i,className:s,passthrough:a,extraSnapRects:m,onSelectionChange:p,deselectSignal:b,onDragMove:y,onDragEnd:R,clearSignal:C,wireframe:N}){let[L,f]=(0,Ke.useState)(new Set),[g,w]=(0,Ke.useState)(null),[$,U]=(0,Ke.useState)(null),[V,B]=(0,Ke.useState)(null),[q,ye]=(0,Ke.useState)([]),[Z,he]=(0,Ke.useState)(null),[Ge,st]=(0,Ke.useState)(!1),Re=(0,Ke.useRef)(!1),[We,Ee]=(0,Ke.useState)(new Set),qe=(0,Ke.useRef)(new Map),Q=(0,Ke.useRef)(null),me=(0,Ke.useRef)(null),Ye=(0,Ke.useRef)(e);Ye.current=e;let Mt=(0,Ke.useRef)(p);Mt.current=p;let cn=(0,Ke.useRef)(y);cn.current=y;let tn=(0,Ke.useRef)(R);tn.current=R;let $o=(0,Ke.useRef)(b);(0,Ke.useEffect)(()=>{b!==$o.current&&($o.current=b,f(new Set))},[b]);let Sn=(0,Ke.useRef)(C);(0,Ke.useEffect)(()=>{if(C!==void 0&&C!==Sn.current){Sn.current=C;let Y=new Set(Ye.current.map(ue=>ue.id));Y.size>0&&(Ee(Y),f(new Set),me.current=null,fe(()=>{t([]),Ee(new Set)},180))}},[C,t]),(0,Ke.useEffect)(()=>{let Y=ue=>{let xe=ue.target;if(!(xe.tagName==="INPUT"||xe.tagName==="TEXTAREA"||xe.isContentEditable)){if((ue.key==="Backspace"||ue.key==="Delete")&&L.size>0){ue.preventDefault();let ve=new Set(L);Ee(ve),f(new Set),fe(()=>{t(Ye.current.filter(Ze=>!ve.has(Ze.id))),Ee(new Set)},180);return}if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(ue.key)&&L.size>0){ue.preventDefault();let ve=ue.shiftKey?20:1,Ze=ue.key==="ArrowLeft"?-ve:ue.key==="ArrowRight"?ve:0,tt=ue.key==="ArrowUp"?-ve:ue.key==="ArrowDown"?ve:0;t(e.map(Xe=>L.has(Xe.id)?{...Xe,x:Math.max(0,Xe.x+Ze),y:Math.max(0,Xe.y+tt)}:Xe));return}if(ue.key==="Escape"){n?o(null):L.size>0&&f(new Set);return}}};return document.addEventListener("keydown",Y),()=>document.removeEventListener("keydown",Y)},[L,n,e,t,o]);let Ro=(0,Ke.useCallback)(Y=>{if(Y.button!==0||a||Y.target.closest(`.${T.placement}`))return;Y.preventDefault(),Y.stopPropagation();let xe=window.scrollY,$e=Y.clientX,ve=Y.clientY;if(n){me.current="place",i?.(!0);let Ze=!1,tt=$e,Xe=ve,ze=S=>{tt=S.clientX,Xe=S.clientY;let I=Math.abs(tt-$e),z=Math.abs(Xe-ve);if((I>5||z>5)&&(Ze=!0),Ze){let A=Math.min($e,tt),J=Math.min(ve,Xe),le=Math.abs(tt-$e),j=Math.abs(Xe-ve);w({x:A,y:J,w:le,h:j}),B({x:S.clientX+12,y:S.clientY+12,text:`${Math.round(le)} \xD7 ${Math.round(j)}`})}},pe=S=>{window.removeEventListener("mousemove",ze),window.removeEventListener("mouseup",pe),w(null),B(null),me.current=null,i?.(!1);let I=ee[n],z,A,J,le;Ze?(z=Math.min($e,tt),A=Math.min(ve,Xe)+xe,J=Math.max(yl,Math.abs(tt-$e)),le=Math.max(yl,Math.abs(Xe-ve))):(J=I.width,le=I.height,z=$e-J/2,A=ve+xe-le/2),z=Math.max(0,z),A=Math.max(0,A);let j={id:ep(),type:n,x:z,y:A,width:J,height:le,scrollY:xe,timestamp:Date.now()},ie=[...e,j];t(ie),f(new Set([j.id])),o(null)};window.addEventListener("mousemove",ze),window.addEventListener("mouseup",pe)}else{Y.shiftKey||f(new Set),me.current="select";let Ze=!1,tt=ze=>{let pe=Math.abs(ze.clientX-$e),S=Math.abs(ze.clientY-ve);if((pe>4||S>4)&&(Ze=!0),Ze){let I=Math.min($e,ze.clientX),z=Math.min(ve,ze.clientY);U({x:I,y:z,w:Math.abs(ze.clientX-$e),h:Math.abs(ze.clientY-ve)})}},Xe=ze=>{if(window.removeEventListener("mousemove",tt),window.removeEventListener("mouseup",Xe),me.current=null,Ze){let pe=Math.min($e,ze.clientX),S=Math.min(ve,ze.clientY)+xe,I=Math.abs(ze.clientX-$e),z=Math.abs(ze.clientY-ve),A=new Set(Y.shiftKey?L:new Set);for(let J of e){let le=J.y-xe;J.x+J.width>pe&&J.x<pe+I&&J.y+J.height>S&&J.y<S+z&&A.add(J.id)}f(A)}U(null)};window.addEventListener("mousemove",tt),window.addEventListener("mouseup",Xe)}},[n,a,e,t,L]),On=(0,Ke.useCallback)((Y,ue)=>{if(Y.button!==0)return;let xe=Y.target;if(xe.closest(`.${T.handle}`)||xe.closest(`.${T.deleteButton}`))return;Y.preventDefault(),Y.stopPropagation();let $e;Y.shiftKey?($e=new Set(L),$e.has(ue)?$e.delete(ue):$e.add(ue)):L.has(ue)?$e=new Set(L):$e=new Set([ue]),f($e),($e.size!==L.size||[...$e].some(ie=>!L.has(ie)))&&Mt.current?.($e,Y.shiftKey);let Ze=window.scrollY,tt=Y.clientX,Xe=Y.clientY,ze=new Map;for(let ie of e)$e.has(ie.id)&&ze.set(ie.id,{x:ie.x,y:ie.y});me.current="move",i?.(!0);let pe=!1,S=!1,I=e,z=0,A=0,J=new Map;for(let ie of e)ze.has(ie.id)&&J.set(ie.id,{w:ie.width,h:ie.height});let le=ie=>{let Se=ie.clientX-tt,Fe=ie.clientY-Xe;if((Math.abs(Se)>2||Math.abs(Fe)>2)&&(pe=!0),!pe)return;if(ie.altKey&&!S){S=!0;let we=[];for(let ut of e)ze.has(ut.id)&&we.push({...ut,id:ep(),timestamp:Date.now()});I=[...e,...we]}let Je=1/0,se=1/0,nt=-1/0,Te=-1/0;for(let[we,ut]of ze){let Ft=J.get(we);Ft&&(Je=Math.min(Je,ut.x+Se),se=Math.min(se,ut.y+Fe),nt=Math.max(nt,ut.x+Se+Ft.w),Te=Math.max(Te,ut.y+Fe+Ft.h))}let Le={x:Je,y:se,width:nt-Je,height:Te-se},{dx:ae,dy:ot,guides:je}=Jh(Le,I,new Set(ze.keys()),void 0,m);ye(je);let Ie=Se+ae,Qe=Fe+ot;z=Ie,A=Qe,t(I.map(we=>{let ut=ze.get(we.id);return ut?{...we,x:Math.max(0,ut.x+Ie),y:Math.max(0,ut.y+Qe)}:we})),cn.current?.(Ie,Qe)},j=()=>{window.removeEventListener("mousemove",le),window.removeEventListener("mouseup",j),me.current=null,i?.(!1),ye([]),tn.current?.(z,A,pe)};window.addEventListener("mousemove",le),window.addEventListener("mouseup",j)},[L,e,t,i]),mo=(0,Ke.useCallback)((Y,ue,xe)=>{Y.preventDefault(),Y.stopPropagation();let $e=e.find(A=>A.id===ue);if(!$e)return;f(new Set([ue])),me.current="resize",i?.(!0);let ve=Y.clientX,Ze=Y.clientY,tt=$e.width,Xe=$e.height,ze=$e.x,pe=$e.y,S={left:xe.includes("w"),right:xe.includes("e"),top:xe.includes("n"),bottom:xe.includes("s")},I=A=>{let J=A.clientX-ve,le=A.clientY-Ze,j=tt,ie=Xe,Se=ze,Fe=pe;xe.includes("e")&&(j=Math.max(yl,tt+J)),xe.includes("w")&&(j=Math.max(yl,tt-J),Se=ze+tt-j),xe.includes("s")&&(ie=Math.max(yl,Xe+le)),xe.includes("n")&&(ie=Math.max(yl,Xe-le),Fe=pe+Xe-ie);let Je={x:Se,y:Fe,width:j,height:ie},{dx:se,dy:nt,guides:Te}=Jh(Je,Ye.current,new Set([ue]),S,m);ye(Te),se!==0&&(S.right?j+=se:S.left&&(Se+=se,j-=se)),nt!==0&&(S.bottom?ie+=nt:S.top&&(Fe+=nt,ie-=nt)),t(Ye.current.map(Le=>Le.id===ue?{...Le,x:Se,y:Fe,width:j,height:ie}:Le)),B({x:A.clientX+12,y:A.clientY+12,text:`${Math.round(j)} \xD7 ${Math.round(ie)}`})},z=()=>{window.removeEventListener("mousemove",I),window.removeEventListener("mouseup",z),B(null),me.current=null,i?.(!1),ye([])};window.addEventListener("mousemove",I),window.addEventListener("mouseup",z)},[e,t,i]),Po=(0,Ke.useCallback)(Y=>{me.current=null,Ee(ue=>{let xe=new Set(ue);return xe.add(Y),xe}),f(ue=>{let xe=new Set(ue);return xe.delete(Y),xe}),fe(()=>{t(Ye.current.filter(ue=>ue.id!==Y)),Ee(ue=>{let xe=new Set(ue);return xe.delete(Y),xe})},180)},[t]),rr=new Set(["text","hero","button","badge","cta","toast","modal","card","navigation","tabs","input","search","breadcrumb","pricing","testimonial","alert","banner","tag","notification","stat","productCard"]),gn={hero:"Headline text",button:"Button label",badge:"Badge label",cta:"Call to action text",toast:"Notification message",modal:"Dialog title",card:"Card title",navigation:"Brand / nav items",tabs:"Tab labels",input:"Placeholder text",search:"Search placeholder",pricing:"Plan name or price",testimonial:"Quote text",alert:"Alert message",banner:"Banner text",tag:"Tag label",notification:"Notification message",stat:"Metric value",productCard:"Product name"},An=(0,Ke.useCallback)(Y=>{let ue=e.find(xe=>xe.id===Y);ue&&(Re.current=!!ue.text,he(Y),st(!1))},[e]),dn=(0,Ke.useCallback)(()=>{Z&&(st(!0),fe(()=>{he(null),st(!1)},150))},[Z]);(0,Ke.useEffect)(()=>{l&&Z&&dn()},[l]);let eo=(0,Ke.useCallback)(Y=>{Z&&(t(e.map(ue=>ue.id===Z?{...ue,text:Y.trim()||void 0}:ue)),dn())},[Z,e,t,dn]),to=typeof window<"u"?window.scrollY:0,Tr=["nw","ne","se","sw"],Wn=N?"#f97316":"#3c82f7",Pe=[{dir:"n",cls:T.edgeN,arrow:(0,dt.jsx)("svg",{width:"8",height:"6",viewBox:"0 0 8 6",fill:"none",children:(0,dt.jsx)("path",{d:"M4 0.5L1 4.5h6z",fill:Wn})})},{dir:"e",cls:T.edgeE,arrow:(0,dt.jsx)("svg",{width:"6",height:"8",viewBox:"0 0 6 8",fill:"none",children:(0,dt.jsx)("path",{d:"M5.5 4L1.5 1v6z",fill:Wn})})},{dir:"s",cls:T.edgeS,arrow:(0,dt.jsx)("svg",{width:"8",height:"6",viewBox:"0 0 8 6",fill:"none",children:(0,dt.jsx)("path",{d:"M4 5.5L1 1.5h6z",fill:Wn})})},{dir:"w",cls:T.edgeW,arrow:(0,dt.jsx)("svg",{width:"6",height:"8",viewBox:"0 0 6 8",fill:"none",children:(0,dt.jsx)("path",{d:"M0.5 4L4.5 1v6z",fill:Wn})})}];return(0,dt.jsxs)(dt.Fragment,{children:[(0,dt.jsx)("div",{ref:Q,className:`${T.overlay} ${r?"":T.light} ${n?T.placing:""} ${a?T.passthrough:""} ${l?T.overlayExiting:""} ${N?T.wireframe:""}${s?` ${s}`:""}`,"data-feedback-toolbar":!0,onMouseDown:Ro,children:e.map(Y=>{let ue=L.has(Y.id),xe=Jn[Y.type]?.label||Y.type,$e=Y.y-to;return(0,dt.jsxs)("div",{"data-design-placement":Y.id,className:`${T.placement} ${ue?T.selected:""} ${We.has(Y.id)?T.exiting:""}`,style:{left:Y.x,top:$e,width:Y.width,height:Y.height,position:"fixed"},onMouseDown:ve=>On(ve,Y.id),onDoubleClick:()=>An(Y.id),children:[(0,dt.jsx)("span",{className:T.placementLabel,children:xe}),(0,dt.jsx)("span",{className:`${T.placementAnnotation} ${Y.text?T.annotationVisible:""}`,children:(Y.text&&qe.current.set(Y.id,Y.text),Y.text||qe.current.get(Y.id)||"")}),(0,dt.jsx)("div",{className:T.placementContent,children:(0,dt.jsx)(Q5,{type:Y.type,width:Y.width,height:Y.height,text:Y.text})}),(0,dt.jsx)("div",{className:T.deleteButton,onMouseDown:ve=>ve.stopPropagation(),onClick:()=>Po(Y.id),children:"\u2715"}),Tr.map(ve=>(0,dt.jsx)("div",{className:`${T.handle} ${T[`handle${ve.charAt(0).toUpperCase()}${ve.slice(1)}`]}`,onMouseDown:Ze=>mo(Ze,Y.id,ve)},ve)),Pe.map(({dir:ve,cls:Ze,arrow:tt})=>(0,dt.jsx)("div",{className:`${T.edgeHandle} ${Ze}`,onMouseDown:Xe=>mo(Xe,Y.id,ve),children:tt},ve))]},Y.id)})}),Z&&(()=>{let Y=e.find(pe=>pe.id===Z);if(!Y)return null;let ue=Y.y-to,xe=Y.x+Y.width/2,$e=ue-8,ve=ue+Y.height+8,Ze=$e>200,tt=ve<window.innerHeight-100,Xe=Math.max(160,Math.min(window.innerWidth-160,xe)),ze;return Ze?ze={left:Xe,bottom:window.innerHeight-$e}:tt?ze={left:Xe,top:ve}:ze={left:Xe,top:Math.max(80,window.innerHeight/2-80)},(0,dt.jsx)(Di,{element:Jn[Y.type]?.label||Y.type,placeholder:gn[Y.type]||"Label or content text",initialValue:Y.text??"",submitLabel:Re.current?"Save":"Set",onSubmit:eo,onCancel:dn,onDelete:Re.current?()=>{eo("")}:void 0,isExiting:Ge,lightMode:!r,style:ze})})(),g&&(0,dt.jsx)("div",{className:T.drawBox,style:{left:g.x,top:g.y,width:g.w,height:g.h},"data-feedback-toolbar":!0}),$&&(0,dt.jsx)("div",{className:T.selectBox,style:{left:$.x,top:$.y,width:$.w,height:$.h},"data-feedback-toolbar":!0}),V&&(0,dt.jsx)("div",{className:T.sizeIndicator,style:{left:V.x,top:V.y},"data-feedback-toolbar":!0,children:V.text}),q.map((Y,ue)=>(0,dt.jsx)("div",{className:T.guideLine,style:Y.axis==="x"?{position:"fixed",left:Y.pos,top:0,width:1,bottom:0}:{position:"fixed",left:0,top:Y.pos-to,right:0,height:1},"data-feedback-toolbar":!0},`${Y.axis}-${Y.pos}-${ue}`))]})}function G5(e){if(!e)return"";let t=e.scrollTop>2,n=e.scrollTop+e.clientHeight<e.scrollHeight-2;return`${t?T.fadeTop:""} ${n?T.fadeBottom:""}`}var _="currentColor",P="0.5";function Z5({type:e}){switch(e){case"navigation":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"4",width:"18",height:"8",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2.5",y:"7",width:"3",height:"1.5",rx:".5",fill:_,opacity:".4"}),(0,c.jsx)("rect",{x:"7",y:"7",width:"2.5",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"11",y:"7",width:"2.5",height:"1.5",rx:".5",fill:_,opacity:".25"})]});case"header":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"2",width:"18",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3",y:"5.5",width:"8",height:"2",rx:".5",fill:_,opacity:".35"}),(0,c.jsx)("rect",{x:"3",y:"9",width:"12",height:"1",rx:".5",fill:_,opacity:".15"})]});case"hero":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"1",width:"18",height:"14",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"5",width:"10",height:"1.5",rx:".5",fill:_,opacity:".35"}),(0,c.jsx)("rect",{x:"7",y:"8",width:"6",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"7.5",y:"10.5",width:"5",height:"2.5",rx:"1",stroke:_,strokeWidth:P})]});case"section":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"1",width:"18",height:"14",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3",y:"4",width:"6",height:"1",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"3",y:"6.5",width:"14",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"3",y:"9",width:"10",height:"1",rx:".5",fill:_,opacity:".15"})]});case"sidebar":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"1",width:"7",height:"14",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2.5",y:"4",width:"4",height:"1",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"2.5",y:"6.5",width:"3.5",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"2.5",y:"9",width:"4",height:"1",rx:".5",fill:_,opacity:".15"})]});case"footer":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"7",width:"18",height:"8",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3",y:"9.5",width:"4",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"9.5",width:"4",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"15",y:"9.5",width:"3",height:"1",rx:".5",fill:_,opacity:".2"})]});case"modal":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"2",width:"14",height:"12",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"4.5",width:"7",height:"1",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"5",y:"7",width:"10",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"11",y:"11",width:"5",height:"2",rx:".75",stroke:_,strokeWidth:P})]});case"divider":return(0,c.jsx)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:(0,c.jsx)("line",{x1:"2",y1:"8",x2:"18",y2:"8",stroke:_,strokeWidth:"0.5",opacity:".3"})});case"card":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"5.5",rx:"1",fill:_,opacity:".04"}),(0,c.jsx)("rect",{x:"4",y:"8.5",width:"8",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"4",y:"11",width:"11",height:"1",rx:".5",fill:_,opacity:".12"})]});case"text":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"4",width:"14",height:"1.5",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"2",y:"7",width:"11",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"2",y:"9.5",width:"13",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"2",y:"12",width:"8",height:"1",rx:".5",fill:_,opacity:".12"})]});case"image":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"2",y1:"2",x2:"18",y2:"14",stroke:_,strokeWidth:".3",opacity:".25"}),(0,c.jsx)("line",{x1:"18",y1:"2",x2:"2",y2:"14",stroke:_,strokeWidth:".3",opacity:".25"})]});case"video":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M8.5 5.5v5l4.5-2.5z",stroke:_,strokeWidth:P,fill:_,opacity:".15"})]});case"table":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"2",width:"18",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"1",y1:"5.5",x2:"19",y2:"5.5",stroke:_,strokeWidth:".3",opacity:".25"}),(0,c.jsx)("line",{x1:"1",y1:"9",x2:"19",y2:"9",stroke:_,strokeWidth:".3",opacity:".25"}),(0,c.jsx)("line",{x1:"7",y1:"2",x2:"7",y2:"14",stroke:_,strokeWidth:".3",opacity:".25"}),(0,c.jsx)("line",{x1:"13",y1:"2",x2:"13",y2:"14",stroke:_,strokeWidth:".3",opacity:".25"})]});case"grid":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1.5",y:"2",width:"7",height:"5.5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"11.5",y:"2",width:"7",height:"5.5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"1.5",y:"9.5",width:"7",height:"5.5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"11.5",y:"9.5",width:"7",height:"5.5",rx:"1",stroke:_,strokeWidth:P})]});case"list":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"3.5",cy:"4.5",r:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"4",width:"10",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"3.5",cy:"8",r:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"7.5",width:"8",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"3.5",cy:"11.5",r:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"11",width:"11",height:"1",rx:".5",fill:_,opacity:".2"})]});case"chart":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"9",width:"2.5",height:"4",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"7",y:"6",width:"2.5",height:"7",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"11",y:"3",width:"2.5",height:"10",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"15",y:"5",width:"2.5",height:"8",rx:".5",fill:_,opacity:".2"})]});case"accordion":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1.5",y:"2",width:"17",height:"4",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3",y:"3.5",width:"6",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"1.5",y:"7.5",width:"17",height:"3",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"1.5",y:"12",width:"17",height:"3",rx:"1",stroke:_,strokeWidth:P})]});case"carousel":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"2",width:"14",height:"10",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M1.5 7L3 8.5 1.5 10",stroke:_,strokeWidth:P,opacity:".35"}),(0,c.jsx)("path",{d:"M18.5 7L17 8.5 18.5 10",stroke:_,strokeWidth:P,opacity:".35"}),(0,c.jsx)("circle",{cx:"8.5",cy:"14",r:".6",fill:_,opacity:".35"}),(0,c.jsx)("circle",{cx:"10",cy:"14",r:".6",fill:_,opacity:".15"}),(0,c.jsx)("circle",{cx:"11.5",cy:"14",r:".6",fill:_,opacity:".15"})]});case"button":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"5",width:"14",height:"6",rx:"2",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"7.5",width:"7",height:"1",rx:".5",fill:_,opacity:".25"})]});case"input":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"4",width:"5.5",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"2",y:"6.5",width:"16",height:"5.5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3.5",y:"8.5",width:"7",height:"1",rx:".5",fill:_,opacity:".12"})]});case"search":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"4.5",width:"16",height:"7",rx:"3.5",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"6",cy:"8",r:"2",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("line",{x1:"7.5",y1:"9.5",x2:"9",y2:"11",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("rect",{x:"9.5",y:"7.5",width:"6",height:"1",rx:".5",fill:_,opacity:".12"})]});case"form":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1.5",width:"5.5",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"2",y:"3.5",width:"16",height:"3",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2",y:"8",width:"7",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"2",y:"10",width:"16",height:"3",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"12",y:"14",width:"6",height:"2",rx:".75",stroke:_,strokeWidth:P})]});case"tabs":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"5",width:"18",height:"10",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"1",y:"2",width:"6",height:"3.5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2.5",y:"3.25",width:"3",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"7",y:"2",width:"6",height:"3.5",rx:".75",stroke:_,strokeWidth:P})]});case"dropdown":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"4",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3.5",y:"3.5",width:"7",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("path",{d:"M15 3.5l1.5 1.5L18 3.5",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("rect",{x:"2",y:"7",width:"16",height:"7",rx:"1",stroke:_,strokeWidth:P,strokeDasharray:"2 1",opacity:".3"})]});case"toggle":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"4",y:"5",width:"12",height:"6",rx:"3",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"13",cy:"8",r:"2",fill:_,opacity:".3"})]});case"avatar":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"10",cy:"8",r:"6",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"10",cy:"6.5",r:"2",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M6.5 13c0-2 1.5-3.5 3.5-3.5s3.5 1.5 3.5 3.5",stroke:_,strokeWidth:P})]});case"badge":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"5",width:"14",height:"6",rx:"3",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6",y:"7.5",width:"8",height:"1",rx:".5",fill:_,opacity:".25"})]});case"breadcrumb":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1.5",y:"7",width:"3.5",height:"1",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("path",{d:"M6.5 7l1 1-1 1",stroke:_,strokeWidth:P,opacity:".2"}),(0,c.jsx)("rect",{x:"9",y:"7",width:"3.5",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("path",{d:"M14 7l1 1-1 1",stroke:_,strokeWidth:P,opacity:".2"}),(0,c.jsx)("rect",{x:"16.5",y:"7",width:"2",height:"1",rx:".5",fill:_,opacity:".15"})]});case"pagination":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"5.5",width:"3.5",height:"5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"5.5",width:"3.5",height:"5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"11",y:"5.5",width:"3.5",height:"5",rx:"1",fill:_,opacity:".15",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"15.5",y:"5.5",width:"3.5",height:"5",rx:"1",stroke:_,strokeWidth:P})]});case"progress":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"7",width:"16",height:"2",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2",y:"7",width:"10",height:"2",rx:"1",fill:_,opacity:".2"})]});case"toast":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"4",width:"16",height:"8",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"5",cy:"8",r:"1.5",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("rect",{x:"8",y:"6.5",width:"7",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"8",y:"9",width:"5",height:"1",rx:".5",fill:_,opacity:".12"})]});case"tooltip":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"3",width:"14",height:"7",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5.5",y:"5.5",width:"9",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("path",{d:"M9 10l1 2.5 1-2.5",stroke:_,strokeWidth:P})]});case"pricing":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6",y:"3",width:"8",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"7",y:"5.5",width:"6",height:"2",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"5",y:"9",width:"10",height:"1",rx:".5",fill:_,opacity:".1"}),(0,c.jsx)("rect",{x:"5",y:"11",width:"10",height:"1",rx:".5",fill:_,opacity:".1"}),(0,c.jsx)("rect",{x:"6",y:"13",width:"8",height:"1.5",rx:".5",fill:_,opacity:".2"})]});case"testimonial":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("text",{x:"4",y:"5.5",fontSize:"4",fill:_,opacity:".2",fontFamily:"serif",children:"\u201C"}),(0,c.jsx)("rect",{x:"4",y:"7",width:"12",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"4",y:"9",width:"9",height:"1",rx:".5",fill:_,opacity:".12"}),(0,c.jsx)("circle",{cx:"5.5",cy:"12.5",r:"1.5",stroke:_,strokeWidth:P,opacity:".25"}),(0,c.jsx)("rect",{x:"8",y:"12",width:"5",height:"1",rx:".5",fill:_,opacity:".15"})]});case"cta":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"2",width:"18",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"4.5",width:"10",height:"1.5",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"6",y:"7.5",width:"8",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"7",y:"10",width:"6",height:"2.5",rx:"1",stroke:_,strokeWidth:P})]});case"alert":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"4",width:"16",height:"8",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"6",cy:"8",r:"2",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("line",{x1:"6",y1:"7",x2:"6",y2:"8.5",stroke:_,strokeWidth:"0.6",opacity:".5"}),(0,c.jsx)("circle",{cx:"6",cy:"9.3",r:".3",fill:_,opacity:".5"}),(0,c.jsx)("rect",{x:"9.5",y:"7",width:"6",height:"1",rx:".5",fill:_,opacity:".2"})]});case"banner":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"5",width:"18",height:"6",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"4",y:"7.5",width:"8",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"14",y:"7",width:"3.5",height:"2",rx:".75",stroke:_,strokeWidth:P})]});case"stat":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"2",width:"14",height:"12",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6",y:"4.5",width:"8",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"5",y:"7",width:"10",height:"2.5",rx:".5",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"7",y:"11",width:"6",height:"1",rx:".5",fill:_,opacity:".12"})]});case"stepper":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"4",cy:"8",r:"2",fill:_,opacity:".2",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"6",y1:"8",x2:"8",y2:"8",stroke:_,strokeWidth:".4",opacity:".3"}),(0,c.jsx)("circle",{cx:"10",cy:"8",r:"2",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"12",y1:"8",x2:"14",y2:"8",stroke:_,strokeWidth:".4",opacity:".3"}),(0,c.jsx)("circle",{cx:"16",cy:"8",r:"2",stroke:_,strokeWidth:P})]});case"tag":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"5",width:"14",height:"6",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5.5",y:"7.5",width:"6",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("line",{x1:"14",y1:"6.5",x2:"15.5",y2:"9.5",stroke:_,strokeWidth:P,opacity:".2"}),(0,c.jsx)("line",{x1:"15.5",y1:"6.5",x2:"14",y2:"9.5",stroke:_,strokeWidth:P,opacity:".2"})]});case"rating":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("path",{d:"M4 5.5l1 2 2.2.3-1.6 1.5.4 2.2L4 10.3l-2 1.2.4-2.2L.8 7.8 3 7.5z",fill:_,opacity:".25"}),(0,c.jsx)("path",{d:"M10 5.5l1 2 2.2.3-1.6 1.5.4 2.2L10 10.3l-2 1.2.4-2.2L6.8 7.8 9 7.5z",fill:_,opacity:".25"}),(0,c.jsx)("path",{d:"M16 5.5l1 2 2.2.3-1.6 1.5.4 2.2L16 10.3l-2 1.2.4-2.2-1.6-1.5 2.2-.3z",stroke:_,strokeWidth:P,opacity:".25"})]});case"map":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"2",y1:"6",x2:"18",y2:"10",stroke:_,strokeWidth:".3",opacity:".15"}),(0,c.jsx)("line",{x1:"7",y1:"2",x2:"11",y2:"14",stroke:_,strokeWidth:".3",opacity:".15"}),(0,c.jsx)("path",{d:"M10 5c-1.7 0-3 1.3-3 3 0 2.5 3 5 3 5s3-2.5 3-5c0-1.7-1.3-3-3-3z",fill:_,opacity:".15",stroke:_,strokeWidth:P})]});case"timeline":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("line",{x1:"5",y1:"2",x2:"5",y2:"14",stroke:_,strokeWidth:".4",opacity:".25"}),(0,c.jsx)("circle",{cx:"5",cy:"4",r:"1.5",fill:_,opacity:".2",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"8",y:"3",width:"8",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("circle",{cx:"5",cy:"8.5",r:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"8",y:"7.5",width:"6",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("circle",{cx:"5",cy:"13",r:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"8",y:"12",width:"7",height:"1",rx:".5",fill:_,opacity:".15"})]});case"fileUpload":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"2",width:"14",height:"12",rx:"1.5",stroke:_,strokeWidth:P,strokeDasharray:"2 1"}),(0,c.jsx)("path",{d:"M10 10V5.5m0 0L7.5 8m2.5-2.5L12.5 8",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("rect",{x:"7",y:"11.5",width:"6",height:"1",rx:".5",fill:_,opacity:".15"})]});case"codeBlock":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"4",cy:"4",r:".6",fill:_,opacity:".3"}),(0,c.jsx)("circle",{cx:"5.5",cy:"4",r:".6",fill:_,opacity:".3"}),(0,c.jsx)("circle",{cx:"7",cy:"4",r:".6",fill:_,opacity:".3"}),(0,c.jsx)("rect",{x:"4",y:"7",width:"7",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"6",y:"9",width:"5",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"4",y:"11",width:"8",height:"1",rx:".5",fill:_,opacity:".12"})]});case"calendar":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"3",width:"16",height:"12",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("line",{x1:"2",y1:"6.5",x2:"18",y2:"6.5",stroke:_,strokeWidth:".4",opacity:".25"}),(0,c.jsx)("rect",{x:"5",y:"4",width:"1",height:"1.5",rx:".3",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"14",y:"4",width:"1",height:"1.5",rx:".3",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"7",cy:"9",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"10",cy:"9",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"13",cy:"9",r:".6",fill:_,opacity:".3"}),(0,c.jsx)("circle",{cx:"7",cy:"12",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"10",cy:"12",r:".6",fill:_,opacity:".2"})]});case"notification":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"3",width:"16",height:"10",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"5.5",cy:"8",r:"2",stroke:_,strokeWidth:P,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"6",width:"6",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"8.5",width:"4.5",height:"1",rx:".5",fill:_,opacity:".12"}),(0,c.jsx)("circle",{cx:"16.5",cy:"4.5",r:"1.5",fill:_,opacity:".25"})]});case"productCard":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"1",width:"14",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3",y:"1",width:"14",height:"6",rx:"1",fill:_,opacity:".04"}),(0,c.jsx)("rect",{x:"5",y:"8.5",width:"7",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"5",y:"10.5",width:"4",height:"1.5",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"12",y:"12",width:"4",height:"2",rx:".75",stroke:_,strokeWidth:P})]});case"profile":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"10",cy:"5",r:"3",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"10",width:"10",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"7",y:"12.5",width:"6",height:"1",rx:".5",fill:_,opacity:".12"})]});case"drawer":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"9",y:"1",width:"10",height:"14",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"10.5",y:"4",width:"5",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"10.5",y:"6.5",width:"7",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"10.5",y:"9",width:"6",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"1",y:"1",width:"7",height:"14",rx:"1",stroke:_,strokeWidth:P,opacity:".15"})]});case"popover":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"2",width:"14",height:"9",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"4.5",width:"8",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"5",y:"7",width:"6",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("path",{d:"M9 11l1 2.5 1-2.5",stroke:_,strokeWidth:P})]});case"logo":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"3",width:"10",height:"10",rx:"2",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M5 9.5l2-4 2 4",stroke:_,strokeWidth:P,opacity:".3"}),(0,c.jsx)("rect",{x:"14",y:"6",width:"4",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"14",y:"8.5",width:"3",height:"1",rx:".5",fill:_,opacity:".12"})]});case"faq":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("text",{x:"2.5",y:"5.5",fontSize:"4",fill:_,opacity:".3",fontWeight:"bold",children:"?"}),(0,c.jsx)("rect",{x:"7",y:"3",width:"10",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"7",y:"5.5",width:"8",height:"1",rx:".5",fill:_,opacity:".12"}),(0,c.jsx)("text",{x:"2.5",y:"11.5",fontSize:"4",fill:_,opacity:".3",fontWeight:"bold",children:"?"}),(0,c.jsx)("rect",{x:"7",y:"9",width:"9",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"7",y:"11.5",width:"7",height:"1",rx:".5",fill:_,opacity:".12"})]});case"gallery":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1.5",y:"1.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"7.5",y:"1.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"13.5",y:"1.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"1.5",y:"9.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"7.5",y:"9.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"13.5",y:"9.5",width:"5",height:"5",rx:".75",stroke:_,strokeWidth:P})]});case"checkbox":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"5",y:"4",width:"8",height:"8",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M7.5 8l1.5 1.5 3-3",stroke:_,strokeWidth:P,opacity:".35"})]});case"radio":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"10",cy:"8",r:"4",stroke:_,strokeWidth:P}),(0,c.jsx)("circle",{cx:"10",cy:"8",r:"2",fill:_,opacity:".3"})]});case"slider":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"7.5",width:"16",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"2",y:"7.5",width:"10",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("circle",{cx:"12",cy:"8",r:"2.5",stroke:_,strokeWidth:P})]});case"datePicker":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"5",rx:"1",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"3.5",y:"3",width:"5",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"14",y:"2.5",width:"2.5",height:"2",rx:".5",fill:_,opacity:".12"}),(0,c.jsx)("rect",{x:"2",y:"7",width:"16",height:"8",rx:"1",stroke:_,strokeWidth:P,strokeDasharray:"2 1",opacity:".3"}),(0,c.jsx)("circle",{cx:"6",cy:"10",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"10",cy:"10",r:".6",fill:_,opacity:".3"}),(0,c.jsx)("circle",{cx:"14",cy:"10",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"6",cy:"13",r:".6",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"10",cy:"13",r:".6",fill:_,opacity:".2"})]});case"skeleton":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"16",height:"3",rx:"1",fill:_,opacity:".08"}),(0,c.jsx)("rect",{x:"2",y:"7",width:"10",height:"2",rx:".75",fill:_,opacity:".08"}),(0,c.jsx)("rect",{x:"2",y:"11",width:"13",height:"2",rx:".75",fill:_,opacity:".08"})]});case"chip":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"1.5",y:"5",width:"10",height:"6",rx:"3",fill:_,opacity:".08",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"4",y:"7.5",width:"4",height:"1",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("line",{x1:"9.5",y1:"6.5",x2:"10.5",y2:"9.5",stroke:_,strokeWidth:P,opacity:".2"}),(0,c.jsx)("line",{x1:"10.5",y1:"6.5",x2:"9.5",y2:"9.5",stroke:_,strokeWidth:P,opacity:".2"}),(0,c.jsx)("rect",{x:"13",y:"5",width:"5.5",height:"6",rx:"3",stroke:_,strokeWidth:P,opacity:".25"})]});case"icon":return(0,c.jsx)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:(0,c.jsx)("path",{d:"M10 3l1.5 3 3.5.5-2.5 2.5.5 3.5L10 11l-3 1.5.5-3.5L5 6.5l3.5-.5z",stroke:_,strokeWidth:P,opacity:".3"})});case"spinner":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"10",cy:"8",r:"5",stroke:_,strokeWidth:P,opacity:".12"}),(0,c.jsx)("path",{d:"M10 3a5 5 0 0 1 5 5",stroke:_,strokeWidth:P,opacity:".35",strokeLinecap:"round"})]});case"feature":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"2",width:"5",height:"5",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("path",{d:"M4.5 3.5v3m-1.5-1.5h3",stroke:_,strokeWidth:P,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"2.5",width:"8",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"5.5",width:"6",height:"1",rx:".5",fill:_,opacity:".12"}),(0,c.jsx)("rect",{x:"2",y:"10",width:"5",height:"5",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"9",y:"10.5",width:"7",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"9",y:"13.5",width:"5",height:"1",rx:".5",fill:_,opacity:".12"})]});case"team":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("circle",{cx:"5",cy:"5",r:"2.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"2.5",y:"9",width:"5",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"15",cy:"5",r:"2.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"12.5",y:"9",width:"5",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("circle",{cx:"10",cy:"5",r:"2.5",stroke:_,strokeWidth:P,opacity:".5"}),(0,c.jsx)("rect",{x:"7.5",y:"9",width:"5",height:"1",rx:".5",fill:_,opacity:".15"}),(0,c.jsx)("rect",{x:"4",y:"12",width:"12",height:"1",rx:".5",fill:_,opacity:".1"})]});case"login":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"3",y:"1",width:"14",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6",y:"3",width:"8",height:"1.5",rx:".5",fill:_,opacity:".25"}),(0,c.jsx)("rect",{x:"5",y:"5.5",width:"10",height:"3",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"5",y:"9.5",width:"10",height:"3",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"6.5",y:"13.5",width:"7",height:"2",rx:".75",fill:_,opacity:".2"})]});case"contact":return(0,c.jsxs)("svg",{viewBox:"0 0 20 16",width:"20",height:"16",fill:"none",children:[(0,c.jsx)("rect",{x:"2",y:"1",width:"16",height:"14",rx:"1.5",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"4",y:"3",width:"5",height:"1",rx:".5",fill:_,opacity:".2"}),(0,c.jsx)("rect",{x:"4",y:"5",width:"12",height:"2.5",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"4",y:"8.5",width:"12",height:"4",rx:".75",stroke:_,strokeWidth:P}),(0,c.jsx)("rect",{x:"11",y:"13.5",width:"5",height:"1.5",rx:".5",fill:_,opacity:".2"})]});default:return null}}function J5({activeType:e,onSelect:t,onDragStart:n,scrollRef:o,fadeClass:r,blankCanvas:l}){return(0,c.jsx)("div",{ref:o,className:`${T.placeScroll} ${r||""}`,children:Fp.map(i=>(0,c.jsxs)("div",{className:T.paletteSection,children:[(0,c.jsx)("div",{className:T.paletteSectionTitle,children:i.section}),i.items.map(s=>(0,c.jsxs)("div",{className:`${T.paletteItem} ${e===s.type?T.active:""} ${l?T.wireframe:""}`,onClick:()=>t(s.type),onMouseDown:a=>{a.button===0&&n(s.type,a)},children:[(0,c.jsx)("div",{className:T.paletteItemIcon,children:(0,c.jsx)(Z5,{type:s.type})}),(0,c.jsx)("span",{className:T.paletteItemLabel,children:s.label})]},s.type))]},i.section))})}function e2({value:e,suffix:t}){let[n,o]=(0,St.useState)(null),[r,l]=(0,St.useState)(t),[i,s]=(0,St.useState)("up"),a=(0,St.useRef)(e),m=(0,St.useRef)(t),p=(0,St.useRef)(),b=n!==null&&r!==t;return(0,St.useEffect)(()=>{if(e!==a.current){if(e===0){a.current=e,m.current=t,o(null);return}s(e>a.current?"up":"down"),o(a.current),l(m.current),a.current=e,m.current=t,clearTimeout(p.current),p.current=fe(()=>o(null),250)}else m.current=t},[e,t]),n===null?(0,c.jsxs)(c.Fragment,{children:[e,t?` ${t}`:""]}):b?(0,c.jsxs)("span",{className:T.rollingWrap,children:[(0,c.jsxs)("span",{style:{visibility:"hidden"},children:[e," ",t]}),(0,c.jsxs)("span",{className:`${T.rollingNum} ${i==="up"?T.exitUp:T.exitDown}`,children:[n," ",r]},`o${n}-${e}`),(0,c.jsxs)("span",{className:`${T.rollingNum} ${i==="up"?T.enterUp:T.enterDown}`,children:[e," ",t]},`n${e}`)]}):(0,c.jsxs)(c.Fragment,{children:[(0,c.jsxs)("span",{className:T.rollingWrap,children:[(0,c.jsx)("span",{style:{visibility:"hidden"},children:e}),(0,c.jsx)("span",{className:`${T.rollingNum} ${i==="up"?T.exitUp:T.exitDown}`,children:n},`o${n}-${e}`),(0,c.jsx)("span",{className:`${T.rollingNum} ${i==="up"?T.enterUp:T.enterDown}`,children:e},`n${e}`)]}),t?` ${t}`:""]})}function t2({activeType:e,onSelect:t,isDarkMode:n,sectionCount:o,onDetectSections:r,visible:l,onExited:i,placementCount:s,onClearPlacements:a,onDragStart:m,blankCanvas:p,onBlankCanvasChange:b,wireframePurpose:y,onWireframePurposeChange:R,Tooltip:C}){let[N,L]=(0,St.useState)(!1),[f,g]=(0,St.useState)("exit"),[w,$]=(0,St.useState)(!1),[U,V]=(0,St.useState)(!0),B=(0,St.useRef)(0),q=(0,St.useRef)(""),ye=(0,St.useRef)(0),Z=(0,St.useRef)(),he=(0,St.useRef)(null),[Ge,st]=(0,St.useState)("");(0,St.useEffect)(()=>(l?(L(!0),clearTimeout(Z.current),cancelAnimationFrame(ye.current),ye.current=kl(()=>{ye.current=kl(()=>{g("enter")})})):(cancelAnimationFrame(ye.current),g("exit"),clearTimeout(Z.current),Z.current=fe(()=>{L(!1),i?.()},200)),()=>cancelAnimationFrame(ye.current)),[l]);let Re=s>0||o>0,We=s+o;if(We>0&&(B.current=We,q.current=p?We===1?"Component":"Components":We===1?"Change":"Changes"),(0,St.useEffect)(()=>{if(Re)w?V(!1):(V(!0),$(!0),kl(()=>{kl(()=>{V(!1)})}));else{V(!0);let qe=fe(()=>$(!1),300);return()=>clearTimeout(qe)}},[Re]),(0,St.useEffect)(()=>{if(!N)return;let qe=he.current;if(!qe)return;let Q=()=>st(G5(qe));Q(),qe.addEventListener("scroll",Q,{passive:!0});let me=new ResizeObserver(Q);return me.observe(qe),()=>{qe.removeEventListener("scroll",Q),me.disconnect()}},[N]),!N)return null;let Ee=[];return s>0&&Ee.push("placed"),o>0&&Ee.push("captured"),(0,c.jsxs)("div",{className:`${T.palette} ${T[f]} ${n?"":T.light}`,"data-feedback-toolbar":!0,"data-agentation-palette":!0,onClick:qe=>qe.stopPropagation(),onMouseDown:qe=>qe.stopPropagation(),onTransitionEnd:qe=>{qe.target===qe.currentTarget&&(l||(clearTimeout(Z.current),L(!1),g("exit"),i?.()))},children:[(0,c.jsxs)("div",{className:T.paletteHeader,children:[(0,c.jsx)("div",{className:T.paletteHeaderTitle,children:"Layout Mode"}),(0,c.jsxs)("div",{className:T.paletteHeaderDesc,children:["Rearrange and resize existing elements, add new components, and explore layout ideas. Agent results may vary."," ",(0,c.jsx)("a",{href:"https://agentation.dev/features#layout-mode",target:"_blank",rel:"noopener noreferrer",children:"Learn more."})]})]}),(0,c.jsxs)("div",{className:`${T.canvasToggle} ${p?T.active:""}`,onClick:()=>b(!p),children:[(0,c.jsx)("span",{className:T.canvasToggleIcon,children:(0,c.jsxs)("svg",{viewBox:"0 0 14 14",width:"14",height:"14",fill:"none",children:[(0,c.jsx)("rect",{x:"1",y:"1",width:"12",height:"12",rx:"2",stroke:"currentColor",strokeWidth:"1"}),(0,c.jsx)("circle",{cx:"4.5",cy:"4.5",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"7",cy:"4.5",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"9.5",cy:"4.5",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"4.5",cy:"7",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"7",cy:"7",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"9.5",cy:"7",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"4.5",cy:"9.5",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"7",cy:"9.5",r:"0.8",fill:"currentColor",opacity:".6"}),(0,c.jsx)("circle",{cx:"9.5",cy:"9.5",r:"0.8",fill:"currentColor",opacity:".6"})]})}),(0,c.jsx)("span",{className:T.canvasToggleLabel,children:"Wireframe New Page"})]}),(0,c.jsx)("div",{className:`${T.wireframePurposeWrap} ${p?"":T.collapsed}`,children:(0,c.jsx)("div",{className:T.wireframePurposeInner,children:(0,c.jsx)("textarea",{className:T.wireframePurposeInput,placeholder:"Describe this page to provide additional context for your agent.",value:y,onChange:qe=>R(qe.target.value),rows:2})})}),(0,c.jsx)(J5,{activeType:e,onSelect:t,onDragStart:m,scrollRef:he,fadeClass:Ge,blankCanvas:p}),w&&(0,c.jsx)("div",{className:`${T.paletteFooterWrap} ${U?T.footerHidden:""}`,children:(0,c.jsx)("div",{className:T.paletteFooterInner,children:(0,c.jsx)("div",{className:T.paletteFooterInnerContent,children:(0,c.jsxs)("div",{className:T.paletteFooter,children:[(0,c.jsx)("span",{className:T.paletteFooterCount,children:(0,c.jsx)(e2,{value:B.current,suffix:q.current})}),(0,c.jsx)("button",{className:T.paletteFooterClear,onClick:a,children:"Clear"})]})})})})]})}function Ml(e){if(e.parentElement)return e.parentElement;let t=e.getRootNode();return t instanceof ShadowRoot?t.host:null}function en(e,t){let n=e;for(;n;){if(n.matches(t))return n;n=Ml(n)}return null}function n2(e){return e.getRootNode()instanceof ShadowRoot}function o2(e){let t=e.getRootNode();return t instanceof ShadowRoot?t.host:null}function jp(e,t=4){let n=[],o=e,r=0;for(;o&&r<t;){let l=o.tagName.toLowerCase();if(l==="html"||l==="body")break;let i=l;if(o.id)i=`#${o.id}`;else if(o.className&&typeof o.className=="string"){let a=o.className.split(/\s+/).find(m=>m.length>2&&!m.match(/^[a-z]{1,2}$/)&&!m.match(/[A-Z0-9]{5,}/));a&&(i=`.${a.split("_")[0]}`)}let s=Ml(o);!o.parentElement&&s&&(i=`\u27E8shadow\u27E9 ${i}`),n.unshift(i),o=s,r++}return n.join(" > ")}function $r(e){let t=jp(e);if(e.dataset.element)return{name:e.dataset.element,path:t};let n=e.tagName.toLowerCase();if(["path","circle","rect","line","g"].includes(n)){let o=en(e,"svg");if(o){let r=Ml(o);if(r instanceof HTMLElement)return{name:`graphic in ${$r(r).name}`,path:t}}return{name:"graphic element",path:t}}if(n==="svg"){let o=Ml(e);if(o?.tagName.toLowerCase()==="button"){let r=o.textContent?.trim();return{name:r?`icon in "${r}" button`:"button icon",path:t}}return{name:"icon",path:t}}if(n==="button"){let o=e.textContent?.trim(),r=e.getAttribute("aria-label");return r?{name:`button [${r}]`,path:t}:{name:o?`button "${o.slice(0,25)}"`:"button",path:t}}if(n==="a"){let o=e.textContent?.trim(),r=e.getAttribute("href");return o?{name:`link "${o.slice(0,25)}"`,path:t}:r?{name:`link to ${r.slice(0,30)}`,path:t}:{name:"link",path:t}}if(n==="input"){let o=e.getAttribute("type")||"text",r=e.getAttribute("placeholder"),l=e.getAttribute("name");return r?{name:`input "${r}"`,path:t}:l?{name:`input [${l}]`,path:t}:{name:`${o} input`,path:t}}if(["h1","h2","h3","h4","h5","h6"].includes(n)){let o=e.textContent?.trim();return{name:o?`${n} "${o.slice(0,35)}"`:n,path:t}}if(n==="p"){let o=e.textContent?.trim();return o?{name:`paragraph: "${o.slice(0,40)}${o.length>40?"...":""}"`,path:t}:{name:"paragraph",path:t}}if(n==="span"||n==="label"){let o=e.textContent?.trim();return o&&o.length<40?{name:`"${o}"`,path:t}:{name:n,path:t}}if(n==="li"){let o=e.textContent?.trim();return o&&o.length<40?{name:`list item: "${o.slice(0,35)}"`,path:t}:{name:"list item",path:t}}if(n==="blockquote")return{name:"blockquote",path:t};if(n==="code"){let o=e.textContent?.trim();return o&&o.length<30?{name:`code: \`${o}\``,path:t}:{name:"code",path:t}}if(n==="pre")return{name:"code block",path:t};if(n==="img"){let o=e.getAttribute("alt");return{name:o?`image "${o.slice(0,30)}"`:"image",path:t}}if(n==="video")return{name:"video",path:t};if(["div","section","article","nav","header","footer","aside","main"].includes(n)){let o=e.className,r=e.getAttribute("role"),l=e.getAttribute("aria-label");if(l)return{name:`${n} [${l}]`,path:t};if(r)return{name:`${r}`,path:t};if(typeof o=="string"&&o){let i=o.split(/[\s_-]+/).map(s=>s.replace(/[A-Z0-9]{5,}.*$/,"")).filter(s=>s.length>2&&!/^[a-z]{1,2}$/.test(s)).slice(0,2);if(i.length>0)return{name:i.join(" "),path:t}}return{name:n==="div"?"container":n,path:t}}return{name:n,path:t}}function wl(e){let t=[],n=e.textContent?.trim();n&&n.length<100&&t.push(n);let o=e.previousElementSibling;if(o){let l=o.textContent?.trim();l&&l.length<50&&t.unshift(`[before: "${l.slice(0,40)}"]`)}let r=e.nextElementSibling;if(r){let l=r.textContent?.trim();l&&l.length<50&&t.push(`[after: "${l.slice(0,40)}"]`)}return t.join(" ")}function r2(e){if(e.dataset.element)return e.dataset.element;let t=e.tagName.toLowerCase();if(t==="path")return"path";if(t==="circle")return"circle";if(t==="rect")return"rectangle";if(t==="line")return"line";if(t==="ellipse")return"ellipse";if(t==="polygon")return"polygon";if(t==="g")return"group";if(t==="svg")return"svg";if(t==="button"){let n=e.textContent?.trim();return n?`button "${n}"`:"button"}if(t==="input")return`input (${e.getAttribute("type")||"text"})`;if(t==="span"||t==="p"||t==="label"){let n=e.textContent?.trim();return n&&n.length<30?`"${n}"`:"text"}if(t==="div"){let n=e.className;if(typeof n=="string"&&n){let o=n.split(/[\s_-]+/).map(r=>r.replace(/[A-Z0-9]{5,}.*$/,"")).filter(r=>r.length>2&&!/^[a-z]{1,2}$/.test(r)).slice(0,2);if(o.length>0)return o.join(" ")}return"container"}return t}function ba(e){let t=Ml(e);if(!t)return"";let r=(e.getRootNode()instanceof ShadowRoot&&e.parentElement?Array.from(e.parentElement.children):Array.from(t.children)).filter(p=>p!==e&&p instanceof HTMLElement);if(r.length===0)return"";let l=r.slice(0,4).map(p=>{let b=p.tagName.toLowerCase(),y=p.className,R="";if(typeof y=="string"&&y){let C=y.split(/\s+/).map(N=>N.replace(/[_][a-zA-Z0-9]{5,}.*$/,"")).find(N=>N.length>2&&!/^[a-z]{1,2}$/.test(N));C&&(R=`.${C}`)}if(b==="button"||b==="a"){let C=p.textContent?.trim().slice(0,15);if(C)return`${b}${R} "${C}"`}return`${b}${R}`}),s=t.tagName.toLowerCase();if(typeof t.className=="string"&&t.className){let p=t.className.split(/\s+/).map(b=>b.replace(/[_][a-zA-Z0-9]{5,}.*$/,"")).find(b=>b.length>2&&!/^[a-z]{1,2}$/.test(b));p&&(s=`.${p}`)}let a=t.children.length,m=a>l.length+1?` (${a} total in ${s})`:"";return l.join(", ")+m}function bl(e){let t=e.className;return typeof t!="string"||!t?"":t.split(/\s+/).filter(o=>o.length>0).map(o=>{let r=o.match(/^([a-zA-Z][a-zA-Z0-9_-]*?)(?:_[a-zA-Z0-9]{5,})?$/);return r?r[1]:o}).filter((o,r,l)=>l.indexOf(o)===r).join(", ")}var Hp=new Set(["none","normal","auto","0px","rgba(0, 0, 0, 0)","transparent","static","visible"]),l2=new Set(["p","span","h1","h2","h3","h4","h5","h6","label","li","td","th","blockquote","figcaption","caption","legend","dt","dd","pre","code","em","strong","b","i","a","time","cite","q"]),i2=new Set(["input","textarea","select"]),s2=new Set(["img","video","canvas","svg"]),a2=new Set(["div","section","article","nav","header","footer","aside","main","ul","ol","form","fieldset"]);function ka(e){if(typeof window>"u")return{};let t=window.getComputedStyle(e),n={},o=e.tagName.toLowerCase(),r;l2.has(o)?r=["color","fontSize","fontWeight","fontFamily","lineHeight"]:o==="button"||o==="a"&&e.getAttribute("role")==="button"?r=["backgroundColor","color","padding","borderRadius","fontSize"]:i2.has(o)?r=["backgroundColor","color","padding","borderRadius","fontSize"]:s2.has(o)?r=["width","height","objectFit","borderRadius"]:a2.has(o)?r=["display","padding","margin","gap","backgroundColor"]:r=["color","fontSize","margin","padding","backgroundColor"];for(let l of r){let i=l.replace(/([A-Z])/g,"-$1").toLowerCase(),s=t.getPropertyValue(i);s&&!Hp.has(s)&&(n[l]=s)}return n}var c2=["color","backgroundColor","borderColor","fontSize","fontWeight","fontFamily","lineHeight","letterSpacing","textAlign","width","height","padding","margin","border","borderRadius","display","position","top","right","bottom","left","zIndex","flexDirection","justifyContent","alignItems","gap","opacity","visibility","overflow","boxShadow","transform"];function Ca(e){if(typeof window>"u")return"";let t=window.getComputedStyle(e),n=[];for(let o of c2){let r=o.replace(/([A-Z])/g,"-$1").toLowerCase(),l=t.getPropertyValue(r);l&&!Hp.has(l)&&n.push(`${r}: ${l}`)}return n.join("; ")}function d2(e){if(!e)return;let t={},n=e.split(";").map(o=>o.trim()).filter(Boolean);for(let o of n){let r=o.indexOf(":");if(r>0){let l=o.slice(0,r).trim(),i=o.slice(r+1).trim();l&&i&&(t[l]=i)}}return Object.keys(t).length>0?t:void 0}function Sa(e){let t=[],n=e.getAttribute("role"),o=e.getAttribute("aria-label"),r=e.getAttribute("aria-describedby"),l=e.getAttribute("tabindex"),i=e.getAttribute("aria-hidden");return n&&t.push(`role="${n}"`),o&&t.push(`aria-label="${o}"`),r&&t.push(`aria-describedby="${r}"`),l&&t.push(`tabindex=${l}`),i==="true"&&t.push("aria-hidden"),e.matches("a, button, input, select, textarea, [tabindex]")&&t.push("focusable"),t.join(", ")}function Ma(e){let t=[],n=e;for(;n&&n.tagName.toLowerCase()!=="html";){let o=n.tagName.toLowerCase(),r=o;if(n.id)r=`${o}#${n.id}`;else if(n.className&&typeof n.className=="string"){let i=n.className.split(/\s+/).map(s=>s.replace(/[_][a-zA-Z0-9]{5,}.*$/,"")).find(s=>s.length>2);i&&(r=`${o}.${i}`)}let l=Ml(n);!n.parentElement&&l&&(r=`\u27E8shadow\u27E9 ${r}`),t.unshift(r),n=l}return t.join(" > ")}var u2=new Set(["nav","header","main","section","article","footer","aside"]),Nu={banner:"Header",navigation:"Navigation",main:"Main Content",contentinfo:"Footer",complementary:"Sidebar",region:"Section"},tp={nav:"Navigation",header:"Header",main:"Main Content",section:"Section",article:"Article",footer:"Footer",aside:"Sidebar"},_2=new Set(["script","style","noscript","link","meta"]),f2=40;function Up(e){let t=e;for(;t&&t!==document.body&&t!==document.documentElement;){let n=window.getComputedStyle(t).position;if(n==="fixed"||n==="sticky")return!0;t=t.parentElement}return!1}function Pr(e){let t=e.tagName.toLowerCase();if(["nav","header","footer","main"].includes(t)&&document.querySelectorAll(t).length===1)return t;if(e.id)return`#${CSS.escape(e.id)}`;if(e.className&&typeof e.className=="string"){let r=e.className.split(/\s+/).filter(l=>l.length>0).find(l=>l.length>2&&!/^[a-zA-Z0-9]{6,}$/.test(l)&&!/^[a-z]{1,2}$/.test(l));if(r){let l=`${t}.${CSS.escape(r)}`;if(document.querySelectorAll(l).length===1)return l}}let n=e.parentElement;if(n){let r=Array.from(n.children).indexOf(e)+1;return`${n===document.body?"body":Pr(n)} > ${t}:nth-child(${r})`}return t}function Ta(e){let t=e.tagName.toLowerCase(),n=e.getAttribute("aria-label");if(n)return n;let o=e.getAttribute("role");if(o&&Nu[o])return Nu[o];if(tp[t])return tp[t];let r=e.querySelector("h1, h2, h3, h4, h5, h6");if(r){let i=r.textContent?.trim();if(i&&i.length<=50)return i;if(i)return i.slice(0,47)+"..."}let{name:l}=$r(e);return l.charAt(0).toUpperCase()+l.slice(1)}function Yp(e){let t=e.className;return typeof t!="string"||!t?null:t.split(/\s+/).map(o=>o.replace(/[_][a-zA-Z0-9]{5,}.*$/,"")).find(o=>o.length>2&&!/^[a-z]{1,2}$/.test(o))||null}function Xp(e){let t=e.textContent?.trim();if(!t)return null;let n=t.replace(/\s+/g," ");return n.length<=30?n:n.slice(0,30)+"\u2026"}function h2(){let e=document.querySelector("main")||document.body,t=Array.from(e.children),n=t;e!==document.body&&t.length<3&&(n=Array.from(document.body.children));let o=[];return n.forEach((r,l)=>{if(!(r instanceof HTMLElement))return;let i=r.tagName.toLowerCase();if(_2.has(i)||r.hasAttribute("data-feedback-toolbar")||r.closest("[data-feedback-toolbar]"))return;let s=window.getComputedStyle(r);if(s.display==="none"||s.visibility==="hidden")return;let a=r.getBoundingClientRect();if(a.height<f2)return;let m=u2.has(i),p=r.getAttribute("role")&&Nu[r.getAttribute("role")],b=i==="div"&&a.height>=60;if(!m&&!p&&!b)return;let y=window.scrollY,R=Up(r),C={x:a.x,y:R?a.y:a.y+y,width:a.width,height:a.height};o.push({id:`rs-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,label:Ta(r),tagName:i,selector:Pr(r),role:r.getAttribute("role"),className:Yp(r),textSnippet:Xp(r),originalRect:C,currentRect:{...C},originalIndex:l,isFixed:R})}),o}function p2(e){let t=window.scrollY,n=e.getBoundingClientRect(),o=Up(e),r={x:n.x,y:o?n.y:n.y+t,width:n.width,height:n.height},l=e.parentElement,i=0;return l&&(i=Array.from(l.children).indexOf(e)),{id:`rs-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,label:Ta(e),tagName:e.tagName.toLowerCase(),selector:Pr(e),role:e.getAttribute("role"),className:Yp(e),textSnippet:Xp(e),originalRect:r,currentRect:{...r},originalIndex:i,isFixed:o}}var np={bg:"rgba(59, 130, 246, 0.08)",border:"rgba(59, 130, 246, 0.5)",pill:"#3b82f6"},op=["nw","n","ne","e","se","s","sw","w"],Ea=24,rp=16,La=5;function lp(e,t,n,o){let r=1/0,l=1/0,i=e.x,s=e.x+e.width,a=e.x+e.width/2,m=e.y,p=e.y+e.height,b=e.y+e.height/2,y=[];for(let B of t)n.has(B.id)||y.push(B.currentRect);o&&y.push(...o);for(let B of y){let q=B.x,ye=B.x+B.width,Z=B.x+B.width/2,he=B.y,Ge=B.y+B.height,st=B.y+B.height/2;for(let Re of[i,s,a])for(let We of[q,ye,Z]){let Ee=We-Re;Math.abs(Ee)<La&&Math.abs(Ee)<Math.abs(r)&&(r=Ee)}for(let Re of[m,p,b])for(let We of[he,Ge,st]){let Ee=We-Re;Math.abs(Ee)<La&&Math.abs(Ee)<Math.abs(l)&&(l=Ee)}}let R=Math.abs(r)<La?r:0,C=Math.abs(l)<La?l:0,N=[],L=new Set,f=i+R,g=s+R,w=a+R,$=m+C,U=p+C,V=b+C;for(let B of y){let q=B.x,ye=B.x+B.width,Z=B.x+B.width/2,he=B.y,Ge=B.y+B.height,st=B.y+B.height/2;for(let Re of[q,Z,ye])for(let We of[f,w,g])if(Math.abs(We-Re)<.5){let Ee=`x:${Math.round(Re)}`;L.has(Ee)||(L.add(Ee),N.push({axis:"x",pos:Re}))}for(let Re of[he,st,Ge])for(let We of[$,V,U])if(Math.abs(We-Re)<.5){let Ee=`y:${Math.round(Re)}`;L.has(Ee)||(L.add(Ee),N.push({axis:"y",pos:Re}))}}return{dx:R,dy:C,guides:N}}var m2=new Set(["script","style","noscript","link","meta","br","hr"]);function ip(e){let t=e;for(;t&&t!==document.body&&t!==document.documentElement;){if(t.closest("[data-feedback-toolbar]"))return null;if(m2.has(t.tagName.toLowerCase())){t=t.parentElement;continue}let n=t.getBoundingClientRect();if(n.width>=rp&&n.height>=rp)return t;t=t.parentElement}return null}function g2({rearrangeState:e,onChange:t,isDarkMode:n,exiting:o,className:r,blankCanvas:l,extraSnapRects:i,onSelectionChange:s,deselectSignal:a,onDragMove:m,onDragEnd:p,clearSignal:b}){let{sections:y}=e,R=(0,ke.useRef)(e);R.current=e;let[C,N]=(0,ke.useState)(new Set),[L,f]=(0,ke.useState)(!1),g=(0,ke.useRef)(b);(0,ke.useEffect)(()=>{b!==void 0&&b!==g.current&&(g.current=b,y.length>0&&f(!0))},[b,y.length]);let w=(0,ke.useRef)(a);(0,ke.useEffect)(()=>{a!==w.current&&(w.current=a,N(new Set))},[a]);let[$,U]=(0,ke.useState)(null),[V,B]=(0,ke.useState)(!1),q=(0,ke.useRef)(!1),ye=(0,ke.useCallback)(S=>{let I=y.find(z=>z.id===S);I&&(q.current=!!I.note,U(S),B(!1))},[y]),Z=(0,ke.useCallback)(()=>{$&&(B(!0),fe(()=>{U(null),B(!1)},150))},[$]),he=(0,ke.useCallback)(S=>{$&&(t({...e,sections:y.map(I=>I.id===$?{...I,note:S.trim()||void 0}:I)}),Z())},[$,y,e,t,Z]);(0,ke.useEffect)(()=>{o&&$&&Z()},[o]);let[Ge,st]=(0,ke.useState)(new Set),Re=(0,ke.useRef)(new Map),[We,Ee]=(0,ke.useState)(null),[qe,Q]=(0,ke.useState)(null),[me,Ye]=(0,ke.useState)([]),[Mt,cn]=(0,ke.useState)(0),tn=(0,ke.useRef)(null),$o=(0,ke.useRef)(new Set),Sn=(0,ke.useRef)(new Map),[Ro,On]=(0,ke.useState)(new Map),[mo,Po]=(0,ke.useState)(new Map),rr=(0,ke.useRef)(new Set),gn=(0,ke.useRef)(new Map),An=(0,ke.useRef)(s);An.current=s;let dn=(0,ke.useRef)(m);dn.current=m;let eo=(0,ke.useRef)(p);eo.current=p,(0,ke.useEffect)(()=>{l&&N(new Set)},[l]);let[to,Tr]=(0,ke.useState)(()=>!e.sections.some(S=>{let I=S.originalRect,z=S.currentRect;return Math.abs(I.x-z.x)>1||Math.abs(I.y-z.y)>1||Math.abs(I.width-z.width)>1||Math.abs(I.height-z.height)>1}));(0,ke.useEffect)(()=>{if(!to){let S=fe(()=>Tr(!0),380);return()=>clearTimeout(S)}},[]);let Wn=(0,ke.useRef)(new Set);(0,ke.useEffect)(()=>{Wn.current=new Set(y.map(S=>S.selector))},[y]),(0,ke.useEffect)(()=>{let S=()=>cn(window.scrollY);return S(),window.addEventListener("scroll",S,{passive:!0}),window.addEventListener("resize",S,{passive:!0}),()=>{window.removeEventListener("scroll",S),window.removeEventListener("resize",S)}},[]),(0,ke.useEffect)(()=>{let S=I=>{if(tn.current){Ee(null);return}let z=document.elementFromPoint(I.clientX,I.clientY);if(!z){Ee(null);return}if(z.closest("[data-feedback-toolbar]")){Ee(null);return}if(z.closest("[data-design-placement]")){Ee(null);return}if(z.closest("[data-annotation-popup]")){Ee(null);return}let A=ip(z);if(!A){Ee(null);return}for(let le of Wn.current)try{let j=document.querySelector(le);if(j&&(j===A||A.contains(j))){Ee(null);return}}catch{}let J=A.getBoundingClientRect();Ee({x:J.x,y:J.y,w:J.width,h:J.height})};return document.addEventListener("mousemove",S,{passive:!0}),()=>document.removeEventListener("mousemove",S)},[y]),(0,ke.useEffect)(()=>{let S=document.body.style.userSelect;return document.body.style.userSelect="none",()=>{document.body.style.userSelect=S}},[]),(0,ke.useEffect)(()=>{let S=I=>{if(tn.current||I.button!==0)return;let z=I.target;if(!z||z.closest("[data-feedback-toolbar]")||z.closest("[data-design-placement]")||z.closest("[data-annotation-popup]"))return;let A=ip(z),J=!1;if(A)for(let j of Wn.current)try{let ie=document.querySelector(j);if(ie&&(ie===A||A.contains(ie))){J=!0;break}}catch{}let le=!!(I.shiftKey||I.metaKey||I.ctrlKey);if(A&&!J){I.preventDefault(),I.stopPropagation();let j=p2(A),ie=[...y,j],Se=[...e.originalOrder,j.id];t({...e,sections:ie,originalOrder:Se});let Fe=new Set([j.id]);N(Fe),An.current?.(Fe,le),Ee(null);let Je=I.clientX,se=I.clientY,nt={x:j.currentRect.x,y:j.currentRect.y},Te=j.originalRect,Le=!1,ae=0,ot=0;tn.current="move";let je=Qe=>{let we=Qe.clientX-Je,ut=Qe.clientY-se;if(!Le&&(Math.abs(we)>2||Math.abs(ut)>2)&&(Le=!0),!Le)return;let Ft={x:nt.x+we,y:nt.y+ut,width:j.currentRect.width,height:j.currentRect.height},Mn=lp(Ft,ie,new Set([j.id]),i);Ye(Mn.guides);let no=we+Mn.dx,un=ut+Mn.dy;ae=no,ot=un;let go=document.querySelector(`[data-rearrange-section="${j.id}"]`);go&&(go.style.transform=`translate(${no}px, ${un}px)`),On(new Map([[j.id,{x:nt.x+no,y:nt.y+un,width:j.currentRect.width,height:j.currentRect.height}]])),dn.current?.(no,un)},Ie=()=>{window.removeEventListener("mousemove",je),window.removeEventListener("mouseup",Ie),tn.current=null,Ye([]),On(new Map);let Qe=document.querySelector(`[data-rearrange-section="${j.id}"]`);Qe&&(Qe.style.transform=""),Le&&t({...e,sections:ie.map(we=>we.id===j.id?{...we,currentRect:{...we.currentRect,x:Math.max(0,nt.x+ae),y:Math.max(0,nt.y+ot)}}:we),originalOrder:Se}),eo.current?.(ae,ot,Le)};window.addEventListener("mousemove",je),window.addEventListener("mouseup",Ie)}else if(J&&A){I.preventDefault();for(let j of y)try{let ie=document.querySelector(j.selector);if(ie&&ie===A){let Se=new Set([j.id]);N(Se),An.current?.(Se,le);return}}catch{}le||(N(new Set),An.current?.(new Set,!1))}else le||(N(new Set),An.current?.(new Set,!1))};return document.addEventListener("mousedown",S,!0),()=>document.removeEventListener("mousedown",S,!0)},[y,e,t]),(0,ke.useEffect)(()=>{let S=I=>{let z=I.target;if(!(z.tagName==="INPUT"||z.tagName==="TEXTAREA"||z.isContentEditable)){if((I.key==="Backspace"||I.key==="Delete")&&C.size>0){I.preventDefault();let A=new Set(C);st(J=>{let le=new Set(J);for(let j of A)le.add(j);return le}),N(new Set),fe(()=>{let J=R.current;t({...J,sections:J.sections.filter(le=>!A.has(le.id)),originalOrder:J.originalOrder.filter(le=>!A.has(le))}),st(le=>{let j=new Set(le);for(let ie of A)j.delete(ie);return j})},180);return}if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(I.key)&&C.size>0){I.preventDefault();let A=I.shiftKey?20:1,J=I.key==="ArrowLeft"?-A:I.key==="ArrowRight"?A:0,le=I.key==="ArrowUp"?-A:I.key==="ArrowDown"?A:0;t({...e,sections:y.map(j=>C.has(j.id)?{...j,currentRect:{...j.currentRect,x:Math.max(0,j.currentRect.x+J),y:Math.max(0,j.currentRect.y+le)}}:j)});return}I.key==="Escape"&&C.size>0&&N(new Set)}};return document.addEventListener("keydown",S),()=>document.removeEventListener("keydown",S)},[C,y,e,t]);let Pe=(0,ke.useCallback)((S,I)=>{if(S.button!==0)return;let z=S.target;if(z.closest(`.${T.handle}`)||z.closest(`.${T.deleteButton}`))return;S.preventDefault(),S.stopPropagation();let A;S.shiftKey||S.metaKey||S.ctrlKey?(A=new Set(C),A.has(I)?A.delete(I):A.add(I)):C.has(I)?A=new Set(C):A=new Set([I]),N(A),(A.size!==C.size||[...A].some(Le=>!C.has(Le)))&&An.current?.(A,!!(S.shiftKey||S.metaKey||S.ctrlKey));let le=S.clientX,j=S.clientY,ie=new Map;for(let Le of y)A.has(Le.id)&&ie.set(Le.id,{x:Le.currentRect.x,y:Le.currentRect.y});tn.current="move";let Se=!1,Fe=0,Je=0,se=new Map;for(let Le of y)if(A.has(Le.id)){let ae=document.querySelector(`[data-rearrange-section="${Le.id}"]`);se.set(Le.id,{outlineEl:ae,curW:Le.currentRect.width,curH:Le.currentRect.height})}let nt=Le=>{let ae=Le.clientX-le,ot=Le.clientY-j;if(ae===0&&ot===0)return;Se=!0;let je=1/0,Ie=1/0,Qe=-1/0,we=-1/0;for(let[un,{curW:go,curH:Ai}]of se){let It=ie.get(un);if(!It)continue;let yo=It.x+ae,Wi=It.y+ot;je=Math.min(je,yo),Ie=Math.min(Ie,Wi),Qe=Math.max(Qe,yo+go),we=Math.max(we,Wi+Ai)}let ut=lp({x:je,y:Ie,width:Qe-je,height:we-Ie},y,A,i),Ft=ae+ut.dx,Mn=ot+ut.dy;Fe=Ft,Je=Mn,Ye(ut.guides);for(let[,{outlineEl:un}]of se)un&&(un.style.transform=`translate(${Ft}px, ${Mn}px)`);let no=new Map;for(let[un,{curW:go,curH:Ai}]of se){let It=ie.get(un);if(It){let yo={x:Math.max(0,It.x+Ft),y:Math.max(0,It.y+Mn),width:go,height:Ai};no.set(un,yo)}}On(no),dn.current?.(Ft,Mn)},Te=Le=>{window.removeEventListener("mousemove",nt),window.removeEventListener("mouseup",Te),tn.current=null,Ye([]),On(new Map);for(let[,{outlineEl:ae}]of se)ae&&(ae.style.transform="");if(Se){let ae=Le.clientX-le,ot=Le.clientY-j;if(Math.abs(ae)<5&&Math.abs(ot)<5)t({...e,sections:y.map(je=>{let Ie=ie.get(je.id);return Ie?{...je,currentRect:{...je.currentRect,x:Ie.x,y:Ie.y}}:je})});else{t({...e,sections:y.map(je=>{let Ie=ie.get(je.id);return Ie?{...je,currentRect:{...je.currentRect,x:Math.max(0,Ie.x+Fe),y:Math.max(0,Ie.y+Je)}}:je})}),eo.current?.(Fe,Je,!0);return}}eo.current?.(0,0,!1)};window.addEventListener("mousemove",nt),window.addEventListener("mouseup",Te)},[C,y,e,t]),Y=(0,ke.useCallback)((S,I,z)=>{S.preventDefault(),S.stopPropagation();let A=y.find(Te=>Te.id===I);if(!A)return;N(new Set([I])),tn.current="resize";let J=S.clientX,le=S.clientY,j={...A.currentRect},ie=A.originalRect,Se=j.width/j.height,Fe={...j},Je=document.querySelector(`[data-rearrange-section="${I}"]`),se=Te=>{let Le=Te.clientX-J,ae=Te.clientY-le,ot=j.x,je=j.y,Ie=j.width,Qe=j.height;if(z.includes("e")&&(Ie=Math.max(Ea,j.width+Le)),z.includes("w")&&(Ie=Math.max(Ea,j.width-Le),ot=j.x+j.width-Ie),z.includes("s")&&(Qe=Math.max(Ea,j.height+ae)),z.includes("n")&&(Qe=Math.max(Ea,j.height-ae),je=j.y+j.height-Qe),Te.shiftKey)if(z.length===2){let ut=Math.abs(Ie-j.width),Ft=Math.abs(Qe-j.height);ut>Ft?Qe=Ie/Se:Ie=Qe*Se,z.includes("w")&&(ot=j.x+j.width-Ie),z.includes("n")&&(je=j.y+j.height-Qe)}else z==="e"||z==="w"?Qe=Ie/Se:Ie=Qe*Se,z==="w"&&(ot=j.x+j.width-Ie),z==="n"&&(je=j.y+j.height-Qe);Fe={x:ot,y:je,width:Ie,height:Qe},Je&&(Je.style.left=`${ot}px`,Je.style.top=`${je-Mt}px`,Je.style.width=`${Ie}px`,Je.style.height=`${Qe}px`),Q({x:Te.clientX+12,y:Te.clientY+12,text:`${Math.round(Ie)} \xD7 ${Math.round(Qe)}`}),On(new Map([[I,Fe]]))},nt=()=>{window.removeEventListener("mousemove",se),window.removeEventListener("mouseup",nt),Q(null),tn.current=null,On(new Map),t({...e,sections:y.map(Te=>Te.id===I?{...Te,currentRect:Fe}:Te)})};window.addEventListener("mousemove",se),window.addEventListener("mouseup",nt)},[y,e,t,Mt]),ue=(0,ke.useCallback)(S=>{st(I=>{let z=new Set(I);return z.add(S),z}),N(I=>{let z=new Set(I);return z.delete(S),z}),fe(()=>{let I=R.current;t({...I,sections:I.sections.filter(z=>z.id!==S),originalOrder:I.originalOrder.filter(z=>z!==S)}),st(z=>{let A=new Set(z);return A.delete(S),A})},180)},[t]),xe=S=>{let I=S.originalRect,z=S.currentRect;return Math.abs(I.x-z.x)>1||Math.abs(I.y-z.y)>1||Math.abs(I.width-z.width)>1||Math.abs(I.height-z.height)>1},$e=S=>{let I=S.originalRect,z=S.currentRect;return Math.abs(I.x-z.x)>1||Math.abs(I.y-z.y)>1},ve=S=>{let I=S.originalRect,z=S.currentRect;return Math.abs(I.width-z.width)>1||Math.abs(I.height-z.height)>1};for(let S of y)Sn.current.has(S.id)||($e(S)?Sn.current.set(S.id,"move"):ve(S)&&Sn.current.set(S.id,"resize"));for(let S of Sn.current.keys())y.some(I=>I.id===S)||Sn.current.delete(S);let Ze=y.filter(S=>{try{if(Ge.has(S.id)||C.has(S.id))return!0;let I=document.querySelector(S.selector);if(!I)return!1;let z=I.getBoundingClientRect(),A=S.originalRect;return Math.abs(z.width-A.width)+Math.abs(z.height-A.height)<200}catch{return!1}}),tt=Ze.filter(S=>xe(S)),Xe=Ze.filter(S=>!xe(S)),ze=new Set(tt.map(S=>S.id));for(let S of $o.current)ze.has(S)||$o.current.delete(S);let pe=[...ze].sort().join(",");for(let S of tt)gn.current.set(S.id,{currentRect:S.currentRect,originalRect:S.originalRect,isFixed:S.isFixed});return(0,ke.useEffect)(()=>{let S=rr.current;rr.current=ze;let I=new Map;for(let z of S)if(!ze.has(z)){if(!y.some(J=>J.id===z))continue;let A=gn.current.get(z);A&&(I.set(z,{orig:A.originalRect,target:A.currentRect,isFixed:A.isFixed}),gn.current.delete(z))}if(I.size>0){Po(A=>{let J=new Map(A);for(let[le,j]of I)J.set(le,j);return J});let z=fe(()=>{Po(A=>{let J=new Map(A);for(let le of I.keys())J.delete(le);return J})},250);return()=>clearTimeout(z)}},[pe,y]),(0,He.jsxs)(He.Fragment,{children:[(0,He.jsxs)("div",{className:`${T.rearrangeOverlay} ${n?"":T.light} ${o?T.overlayExiting:""}${r?` ${r}`:""}`,"data-feedback-toolbar":!0,children:[We&&(0,He.jsx)("div",{className:T.hoverHighlight,style:{left:We.x,top:We.y,width:We.w,height:We.h}}),Xe.map(S=>{let I=S.currentRect,z=S.isFixed?I.y:I.y-Mt,A=np,J=C.has(S.id);return(0,He.jsxs)("div",{"data-rearrange-section":S.id,className:`${T.sectionOutline} ${J?T.selected:""} ${L||o||Ge.has(S.id)?T.exiting:""}`,style:{left:I.x,top:z,width:I.width,height:I.height,borderColor:A.border,backgroundColor:A.bg,...to?{}:{opacity:0,animation:"none",transition:"none"}},onMouseDown:le=>Pe(le,S.id),onDoubleClick:()=>ye(S.id),children:[(0,He.jsx)("span",{className:T.sectionLabel,style:{backgroundColor:A.pill},children:S.label}),(0,He.jsx)("span",{className:`${T.sectionAnnotation} ${S.note?T.annotationVisible:""}`,children:(S.note&&Re.current.set(S.id,S.note),S.note||Re.current.get(S.id)||"")}),(0,He.jsxs)("span",{className:T.sectionDimensions,children:[Math.round(I.width)," \xD7 ",Math.round(I.height)]}),(0,He.jsx)("div",{className:T.deleteButton,onMouseDown:le=>le.stopPropagation(),onClick:()=>ue(S.id),children:"\u2715"}),op.map(le=>(0,He.jsx)("div",{className:`${T.handle} ${T[`handle${le.charAt(0).toUpperCase()}${le.slice(1)}`]}`,onMouseDown:j=>Y(j,S.id,le)},le))]},S.id)}),tt.map(S=>{let I=S.currentRect,z=S.isFixed?I.y:I.y-Mt,A=C.has(S.id),J=$e(S),le=ve(S);if(l&&!A)return null;let ie=!$o.current.has(S.id);return ie&&$o.current.add(S.id),(0,He.jsxs)("div",{"data-rearrange-section":S.id,className:`${T.ghostOutline} ${A?T.selected:""} ${L||o||Ge.has(S.id)?T.exiting:""}`,style:{left:I.x,top:z,width:I.width,height:I.height,...to?{}:{opacity:0,animation:"none",transition:"none"},...ie?{}:{animation:"none"}},onMouseDown:Se=>Pe(Se,S.id),onDoubleClick:()=>ye(S.id),children:[(0,He.jsx)("span",{className:T.sectionLabel,style:{backgroundColor:np.pill},children:S.label}),(0,He.jsx)("span",{className:`${T.sectionAnnotation} ${S.note?T.annotationVisible:""}`,children:(S.note&&Re.current.set(S.id,S.note),S.note||Re.current.get(S.id)||"")}),(0,He.jsxs)("span",{className:T.sectionDimensions,children:[Math.round(I.width)," \xD7 ",Math.round(I.height)]}),(0,He.jsx)("div",{className:T.deleteButton,onMouseDown:Se=>Se.stopPropagation(),onClick:()=>ue(S.id),children:"\u2715"}),op.map(Se=>(0,He.jsx)("div",{className:`${T.handle} ${T[`handle${Se.charAt(0).toUpperCase()}${Se.slice(1)}`]}`,onMouseDown:Fe=>Y(Fe,S.id,Se)},Se)),(0,He.jsx)("span",{className:T.ghostBadge,children:(()=>{let Se=Sn.current.get(S.id);if(J&&le){let[Fe,Je]=Se==="resize"?["Resize","Move"]:["Move","Resize"];return(0,He.jsxs)(He.Fragment,{children:["Suggested ",Fe," ",(0,He.jsxs)("span",{className:T.ghostBadgeExtra,children:["& ",Je]})]})}return`Suggested ${le?"Resize":"Move"}`})()})]},S.id)})]}),!l&&(()=>{let S=[];for(let I of tt){let z=Ro.get(I.id);S.push({id:I.id,orig:I.originalRect,target:z||I.currentRect,isFixed:I.isFixed,isSelected:C.has(I.id),isExiting:Ge.has(I.id)})}for(let[I,z]of Ro)if(!S.some(A=>A.id===I)){let A=y.find(J=>J.id===I);A&&S.push({id:I,orig:A.originalRect,target:z,isFixed:A.isFixed,isSelected:C.has(I)})}for(let[I,z]of mo)S.some(A=>A.id===I)||S.push({id:I,orig:z.orig,target:z.target,isFixed:z.isFixed,isSelected:!1,isExiting:!0});return S.length===0?null:(0,He.jsxs)("svg",{className:`${T.connectorSvg} ${L||o?T.connectorExiting:""}`,children:[S.map(({id:I,orig:z,target:A,isFixed:J,isSelected:le,isExiting:j})=>{let ie=z.x+z.width/2,Se=(J?z.y:z.y-Mt)+z.height/2,Fe=A.x+A.width/2,Je=(J?A.y:A.y-Mt)+A.height/2,se=Fe-ie,nt=Je-Se,Te=Math.sqrt(se*se+nt*nt);if(Te<2)return null;let Le=Math.min(1,Te/40),ae=Math.min(Te*.3,60),ot=Te>0?-nt/Te:0,je=Te>0?se/Te:0,Ie=(ie+Fe)/2+ot*ae,Qe=(Se+Je)/2+je*ae,we=Ro.has(I),ut=we||le?1:.4,Ft=we||le?1:.5;return(0,He.jsxs)("g",{className:j?T.connectorExiting:"",children:[(0,He.jsx)("path",{className:T.connectorLine,d:`M ${ie} ${Se} Q ${Ie} ${Qe} ${Fe} ${Je}`,fill:"none",stroke:"rgba(59, 130, 246, 0.45)",strokeWidth:"1.5",opacity:ut*Le}),(0,He.jsx)("circle",{className:T.connectorDot,cx:ie,cy:Se,r:4*Le,fill:"rgba(59, 130, 246, 0.8)",stroke:"#fff",strokeWidth:"1.5",opacity:Ft*Le,filter:"url(#connDotShadow)"}),(0,He.jsx)("circle",{className:T.connectorDot,cx:Fe,cy:Je,r:4*Le,fill:"rgba(59, 130, 246, 0.8)",stroke:"#fff",strokeWidth:"1.5",opacity:Ft*Le,filter:"url(#connDotShadow)"})]},`conn-${I}`)}),(0,He.jsx)("defs",{children:(0,He.jsx)("filter",{id:"connDotShadow",x:"-50%",y:"-50%",width:"200%",height:"200%",children:(0,He.jsx)("feDropShadow",{dx:"0",dy:"0.5",stdDeviation:"1",floodOpacity:"0.15"})})})]})})(),$&&(()=>{let S=y.find(Je=>Je.id===$);if(!S)return null;let I=S.currentRect,z=S.isFixed?I.y:I.y-Mt,A=I.x+I.width/2,J=z-8,le=z+I.height+8,j=J>200,ie=le<window.innerHeight-100,Se=Math.max(160,Math.min(window.innerWidth-160,A)),Fe;return j?Fe={left:Se,bottom:window.innerHeight-J}:ie?Fe={left:Se,top:le}:Fe={left:Se,top:Math.max(80,window.innerHeight/2-80)},(0,He.jsx)(Di,{element:S.label,placeholder:"Add a note about this section",initialValue:S.note??"",submitLabel:q.current?"Save":"Set",onSubmit:he,onCancel:Z,onDelete:q.current?()=>{he("")}:void 0,isExiting:V,lightMode:!n,style:Fe})})(),qe&&(0,He.jsx)("div",{className:T.sizeIndicator,style:{left:qe.x,top:qe.y},"data-feedback-toolbar":!0,children:qe.text}),me.map((S,I)=>(0,He.jsx)("div",{className:T.guideLine,style:S.axis==="x"?{position:"fixed",left:S.pos,top:0,width:1,height:"100vh"}:{position:"fixed",left:0,top:S.pos-Mt,width:"100vw",height:1}},`${S.axis}-${S.pos}-${I}`))]})}var $u=new Set(["script","style","noscript","link","meta","br","hr"]);function y2(){let e=document.querySelector("main")||document.body,t=[],n=Array.from(e.children),o=e!==document.body&&n.length<3?Array.from(document.body.children):n;for(let r of o){if(!(r instanceof HTMLElement)||$u.has(r.tagName.toLowerCase())||r.hasAttribute("data-feedback-toolbar"))continue;let l=window.getComputedStyle(r);if(l.display==="none"||l.visibility==="hidden")continue;let i=r.getBoundingClientRect();if(!(i.height<10||i.width<10)){t.push({label:Ta(r),selector:Pr(r),top:i.top,bottom:i.bottom,left:i.left,right:i.right,area:i.width*i.height});for(let s of Array.from(r.children)){if(!(s instanceof HTMLElement)||$u.has(s.tagName.toLowerCase())||s.hasAttribute("data-feedback-toolbar"))continue;let a=window.getComputedStyle(s);if(a.display==="none"||a.visibility==="hidden")continue;let m=s.getBoundingClientRect();m.height<10||m.width<10||t.push({label:Ta(s),selector:Pr(s),top:m.top,bottom:m.bottom,left:m.left,right:m.right,area:m.width*m.height})}}}return t}function x2(e){let t=window.scrollY;return e.map(({label:n,selector:o,rect:r})=>{let l=r.y-t;return{label:n,selector:o,top:l,bottom:l+r.height,left:r.x,right:r.x+r.width,area:r.width*r.height}})}function v2(e){let t=window.scrollY,n=e.y-t,o=e.x;return{top:n,bottom:n+e.height,left:o,right:o+e.width,area:e.width*e.height}}function Ru(e,t){let n=t?x2(t):y2(),o=v2(e),r=null,l=null,i=null,s=null,a=null;for(let C of n){if(Math.abs(C.left-o.left)<2&&Math.abs(C.top-o.top)<2&&Math.abs(C.right-C.left-e.width)<2&&Math.abs(C.bottom-C.top-e.height)<2)continue;C.left<=o.left+2&&C.right>=o.right-2&&C.top<=o.top+2&&C.bottom>=o.bottom-2&&C.area>o.area*1.5&&(!a||C.area<a._area)&&(a={label:C.label,selector:C.selector,_area:C.area});let N=o.right>C.left+5&&o.left<C.right-5,L=o.bottom>C.top+5&&o.top<C.bottom-5;if(N&&C.bottom<=o.top+5){let f=Math.round(o.top-C.bottom);(!r||f<r._dist)&&(r={label:C.label,selector:C.selector,gap:Math.max(0,f),_dist:f})}if(N&&C.top>=o.bottom-5){let f=Math.round(C.top-o.bottom);(!l||f<l._dist)&&(l={label:C.label,selector:C.selector,gap:Math.max(0,f),_dist:f})}if(L&&C.right<=o.left+5){let f=Math.round(o.left-C.right);(!i||f<i._dist)&&(i={label:C.label,selector:C.selector,gap:Math.max(0,f),_dist:f})}if(L&&C.left>=o.right-5){let f=Math.round(C.left-o.right);(!s||f<s._dist)&&(s={label:C.label,selector:C.selector,gap:Math.max(0,f),_dist:f})}}let m=window.innerWidth,p=window.innerHeight,b=b2(e,m),y=C=>C?{label:C.label,selector:C.selector,gap:C.gap}:null,R=w2(o,e,m,p,a?{label:a.label,selector:a.selector,_area:a._area}:null,n);return{above:y(r),below:y(l),left:y(i),right:y(s),alignment:b,containedIn:a?{label:a.label,selector:a.selector}:null,outOfBounds:R}}function w2(e,t,n,o,r,l){let i={},s=!1,a=[];if(e.left<-2&&a.push("left"),e.right>n+2&&a.push("right"),e.top<-2&&a.push("top"),e.bottom>o+2&&a.push("bottom"),a.length>0&&(i.viewport=a,s=!0),r){let m=l.find(p=>p.label===r.label&&p.selector===r.selector&&Math.abs(p.area-r._area)<10);if(m){let p=[];e.left<m.left-2&&p.push("left"),e.right>m.right+2&&p.push("right"),e.top<m.top-2&&p.push("top"),e.bottom>m.bottom+2&&p.push("bottom"),p.length>0&&(i.container={label:r.label,edges:p},s=!0)}}return s?i:null}function b2(e,t){if(e.width/t>.85)return"full-width";let o=e.x+e.width/2,r=t/2,l=o-r,i=t*.08;return Math.abs(l)<i?"center":l<0?"left":"right"}function Qp(e){switch(e){case"full-width":return"full-width";case"center":return"centered";case"left":return"left-aligned";case"right":return"right-aligned"}}function Vp(e,t={}){let n=[];e.above&&n.push(`Below \`${e.above.label}\`${e.above.gap>0?` (${e.above.gap}px gap)`:""}`),e.below&&n.push(`Above \`${e.below.label}\`${e.below.gap>0?` (${e.below.gap}px gap)`:""}`),t.includeLeftRight&&(e.left&&n.push(`Right of \`${e.left.label}\`${e.left.gap>0?` (${e.left.gap}px gap)`:""}`),e.right&&n.push(`Left of \`${e.right.label}\`${e.right.gap>0?` (${e.right.gap}px gap)`:""}`));let o=Qp(e.alignment);return e.containedIn?n.push(`${o.charAt(0).toUpperCase()+o.slice(1)} in \`${e.containedIn.label}\``):n.push(`${o.charAt(0).toUpperCase()+o.slice(1)} in page`),t.includePixelRef&&t.pixelRef&&n.push(`Pixel ref: \`${t.pixelRef}\``),e.outOfBounds&&(e.outOfBounds.viewport&&n.push(`**Outside viewport** (${e.outOfBounds.viewport.join(", ")} edge${e.outOfBounds.viewport.length>1?"s":""})`),e.outOfBounds.container&&n.push(`**Outside \`${e.outOfBounds.container.label}\`** (${e.outOfBounds.container.edges.join(", ")} edge${e.outOfBounds.container.edges.length>1?"s":""})`)),n}function k2(e,t,n){let o=[];e.above&&o.push(`below \`${e.above.label}\``),e.below&&o.push(`above \`${e.below.label}\``),e.left&&o.push(`right of \`${e.left.label}\``),e.right&&o.push(`left of \`${e.right.label}\``),e.containedIn&&o.push(`inside \`${e.containedIn.label}\``),o.push(Qp(e.alignment)),e.outOfBounds?.viewport&&o.push(`**outside viewport** (${e.outOfBounds.viewport.join(", ")})`),e.outOfBounds?.container&&o.push(`**outside \`${e.outOfBounds.container.label}\`** (${e.outOfBounds.container.edges.join(", ")})`);let r=n?`, ${Math.round(n.width)}\xD7${Math.round(n.height)}px`:"";return`at (${Math.round(t.x)}, ${Math.round(t.y)})${r}: ${o.join(", ")}`}var sp=15;function ap(e){if(e.length<2)return[];let t=[],n=new Set;for(let o=0;o<e.length;o++){if(n.has(o))continue;let r=[o];for(let l=o+1;l<e.length;l++)n.has(l)||Math.abs(e[o].rect.y-e[l].rect.y)<sp&&r.push(l);if(r.length>=2){let l=r.map(a=>e[a]);l.sort((a,m)=>a.rect.x-m.rect.x);let i=[];for(let a=0;a<l.length-1;a++)i.push(Math.round(l[a+1].rect.x-(l[a].rect.x+l[a].rect.width)));let s=Math.round(l.reduce((a,m)=>a+m.rect.y,0)/l.length);t.push({labels:l.map(a=>a.label),type:"row",sharedEdge:s,gaps:i,avgGap:i.length?Math.round(i.reduce((a,m)=>a+m,0)/i.length):0}),r.forEach(a=>n.add(a))}}for(let o=0;o<e.length;o++){if(n.has(o))continue;let r=[o];for(let l=o+1;l<e.length;l++)n.has(l)||Math.abs(e[o].rect.x-e[l].rect.x)<sp&&r.push(l);if(r.length>=2){let l=r.map(a=>e[a]);l.sort((a,m)=>a.rect.y-m.rect.y);let i=[];for(let a=0;a<l.length-1;a++)i.push(Math.round(l[a+1].rect.y-(l[a].rect.y+l[a].rect.height)));let s=Math.round(l.reduce((a,m)=>a+m.rect.x,0)/l.length);t.push({labels:l.map(a=>a.label),type:"column",sharedEdge:s,gaps:i,avgGap:i.length?Math.round(i.reduce((a,m)=>a+m,0)/i.length):0}),r.forEach(a=>n.add(a))}}return t}function C2(e){if(e.length<2)return[];let t=ap(e.map(i=>({label:i.label,rect:i.originalRect}))),n=ap(e.map(i=>({label:i.label,rect:i.currentRect}))),o=[],r=new Set;for(let i of t){let s=new Set(i.labels),a=null,m=0;for(let p of n){let b=p.labels.filter(y=>s.has(y)).length;b>=2&&b>m&&(a=p,m=b)}if(a){let p=a.labels.filter(y=>s.has(y)),b=p.join(", ");if(a.type!==i.type){let y=i.type==="row"?"y":"x",R=a.type==="row"?"y":"x";o.push(`**${b}**: ${i.type} (${y}\u2248${i.sharedEdge}, ${i.avgGap}px gaps) \u2192 ${a.type} (${R}\u2248${a.sharedEdge}, ${a.avgGap}px gaps)`)}else if(Math.abs(i.sharedEdge-a.sharedEdge)>20||Math.abs(i.avgGap-a.avgGap)>5){let y=i.type==="row"?"y":"x",R=Math.abs(i.sharedEdge-a.sharedEdge)>20?` ${y}: ${i.sharedEdge} \u2192 ${a.sharedEdge}`:"",C=Math.abs(i.avgGap-a.avgGap)>5?` gaps: ${i.avgGap}px \u2192 ${a.avgGap}px`:"";o.push(`**${b}**: ${i.type} shifted \u2014${R}${C}`)}p.forEach(y=>r.add(y))}else{let p=i.labels.join(", "),b=i.type==="row"?"y":"x";o.push(`**${p}**: ${i.type} (${b}\u2248${i.sharedEdge}) dissolved`),i.labels.forEach(y=>r.add(y))}}for(let i of n){if(i.labels.every(m=>r.has(m))||i.labels.filter(m=>!r.has(m)).length<2)continue;if(!t.some(m=>m.labels.filter(b=>i.labels.includes(b)).length>=2)){let m=i.type==="row"?"y":"x";o.push(`**${i.labels.join(", ")}**: new ${i.type} (${m}\u2248${i.sharedEdge}, ${i.avgGap}px gaps)`),i.labels.forEach(p=>r.add(p))}}let l=e.filter(i=>!r.has(i.label));if(l.length>=2){let i={};for(let s of l){let a=Math.round(s.currentRect.x/5)*5;(i[a]??(i[a]=[])).push(s.label)}for(let[s,a]of Object.entries(i))a.length>=2&&o.push(`**${a.join(", ")}**: shared left edge at x\u2248${s}`)}return o}function Kp(e){if(typeof document>"u")return{viewport:e,contentArea:null};let t=[],n=new Set,o=s=>{n.has(s)||s instanceof HTMLElement&&(s.hasAttribute("data-feedback-toolbar")||$u.has(s.tagName.toLowerCase())||(n.add(s),t.push(s)))},r=document.querySelector("main");r&&o(r);let l=document.querySelector("[role='main']");l&&o(l);for(let s of Array.from(document.body.children))if(o(s),s.children){for(let a of Array.from(s.children))if(o(a),a.children)for(let m of Array.from(a.children))o(m)}let i=null;for(let s of t){let a=s.getBoundingClientRect();if(a.height<50)continue;let m=getComputedStyle(s);if(m.maxWidth&&m.maxWidth!=="none"&&m.maxWidth!=="0px"){(!i||a.width<i.rect.width)&&(i={el:s,rect:a});continue}!i&&a.width<e.width-20&&a.width>100&&(i={el:s,rect:a})}if(i){let{el:s,rect:a}=i;return{viewport:e,contentArea:{width:Math.round(a.width),left:Math.round(a.left),right:Math.round(a.right),centerX:Math.round(a.left+a.width/2),selector:Pr(s)}}}return{viewport:e,contentArea:null}}function S2(e){if(typeof document>"u")return null;let t=document.querySelector(e);if(!t?.parentElement)return null;let n=getComputedStyle(t.parentElement),o={parentDisplay:n.display,parentSelector:Pr(t.parentElement)};return n.display.includes("flex")&&(o.flexDirection=n.flexDirection),n.display.includes("grid")&&n.gridTemplateColumns!=="none"&&(o.gridCols=n.gridTemplateColumns),n.gap&&n.gap!=="normal"&&n.gap!=="0px"&&(o.gap=n.gap),o}function qp(e,t){let n=t.contentArea,o=n?n.width:t.viewport.width,r=n?n.left:0,l=n?n.centerX:Math.round(t.viewport.width/2),i=Math.round(e.x-r),s=Math.round(r+o-(e.x+e.width)),a=(e.width/o*100).toFixed(1),m=e.x+e.width/2,p=Math.abs(m-l)<20,b=e.width/o>.95,y=[];return b?y.push("`width: 100%` of container"):y.push(`left \`${i}px\` in container, right \`${s}px\`, width \`${a}%\` (\`${Math.round(e.width)}px\`)`),p&&!b&&y.push("centered \u2014 `margin-inline: auto`"),y.join(" \u2014 ")}function Gp(e){let{viewport:t,contentArea:n}=e,o=`### Reference Frame
`;if(o+=`- Viewport: \`${t.width}\xD7${t.height}px\`
`,n){let r=n;o+=`- Content area: \`${r.width}px\` wide, left edge at \`x=${r.left}\`, right at \`x=${r.right}\` (\`${r.selector}\`)
`,o+=`- Pixel \u2192 CSS translation:
`,o+=`  - **Horizontal position in container**: \`element.x - ${r.left}\` \u2192 use as \`margin-left\` or \`left\`
`,o+=`  - **Width as % of container**: \`element.width / ${r.width} \xD7 100\` \u2192 use as \`width: X%\`
`,o+="  - **Vertical gap between elements**: `nextElement.y - (prevElement.y + prevElement.height)` \u2192 use as `margin-top` or `gap`\n",o+=`  - **Centered**: if \`|element.centerX - ${r.centerX}| < 20px\` \u2192 use \`margin-inline: auto\`
`}else o+=`- No distinct content container \u2014 elements positioned relative to full viewport
`,o+=`- Pixel \u2192 CSS translation:
`,o+=`  - **Width as % of viewport**: \`element.width / ${t.width} \xD7 100\` \u2192 use as \`width: X%\`
`,o+=`  - **Centered**: if \`|(element.x + element.width/2) - ${Math.round(t.width/2)}| < 20px\` \u2192 use \`margin-inline: auto\`
`;return o+=`
`,o}function M2(e){let t=S2(e);if(!t)return null;let n=`\`${t.parentDisplay}\``;return t.flexDirection&&(n+=`, flex-direction: \`${t.flexDirection}\``),t.gridCols&&(n+=`, grid-template-columns: \`${t.gridCols}\``),t.gap&&(n+=`, gap: \`${t.gap}\``),`Parent: ${n} (\`${t.parentSelector}\`)`}function cp(e,t,n,o="standard"){if(e.length===0)return"";let r=[...e].sort((L,f)=>Math.abs(L.y-f.y)<20?L.x-f.x:L.y-f.y),l="";if(n?.blankCanvas?(l+=`## Wireframe: New Page

`,n.wireframePurpose&&(l+=`> **Purpose:** ${n.wireframePurpose}
>
`),l+=`> ${e.length} component${e.length!==1?"s":""} placed \u2014 this is a standalone wireframe, not related to the current page.
>
> This wireframe is a rough sketch for exploring ideas.

`):l+=`## Design Layout

> ${e.length} component${e.length!==1?"s":""} placed

`,o==="compact")return l+=`### Components
`,r.forEach((L,f)=>{let g=Jn[L.type]?.label||L.type;l+=`${f+1}. **${g}** \u2014 \`${Math.round(L.width)}\xD7${Math.round(L.height)}px\` at \`(${Math.round(L.x)}, ${Math.round(L.y)})\`
`}),l;let i=Kp(t);l+=Gp(i),l+=`### Components
`,r.forEach((L,f)=>{let g=Jn[L.type]?.label||L.type,w={x:L.x,y:L.y,width:L.width,height:L.height};l+=`${f+1}. **${g}** \u2014 \`${Math.round(L.width)}\xD7${Math.round(L.height)}px\` at \`(${Math.round(L.x)}, ${Math.round(L.y)})\`
`;let $=Ru(w),V=Vp($,{includeLeftRight:o==="detailed"||o==="forensic"});for(let q of V)l+=`   - ${q}
`;let B=qp(w,i);B&&(l+=`   - CSS: ${B}
`)}),l+=`
### Layout Analysis
`;let s=[];for(let L of r){let f=s.find(g=>Math.abs(g.y-L.y)<30);f?f.items.push(L):s.push({y:L.y,items:[L]})}if(s.sort((L,f)=>L.y-f.y),s.forEach((L,f)=>{L.items.sort((w,$)=>w.x-$.x);let g=L.items.map(w=>Jn[w.type]?.label||w.type);if(L.items.length===1){let $=L.items[0].width>t.width*.8;l+=`- Row ${f+1} (y\u2248${Math.round(L.y)}): ${g[0]}${$?" \u2014 full width":""}
`}else l+=`- Row ${f+1} (y\u2248${Math.round(L.y)}): ${g.join(" | ")} \u2014 ${L.items.length} items side by side
`}),o==="detailed"||o==="forensic"){l+=`
### Spacing & Gaps
`;for(let L=0;L<r.length-1;L++){let f=r[L],g=r[L+1],w=Jn[f.type]?.label||f.type,$=Jn[g.type]?.label||g.type,U=Math.round(g.y-(f.y+f.height)),V=Math.round(g.x-(f.x+f.width));Math.abs(f.y-g.y)<30?l+=`- ${w} \u2192 ${$}: \`${V}px\` horizontal gap
`:l+=`- ${w} \u2192 ${$}: \`${U}px\` vertical gap
`}if(o==="forensic"&&r.length>2){l+=`
### All Pairwise Gaps
`;for(let L=0;L<r.length;L++)for(let f=L+1;f<r.length;f++){let g=r[L],w=r[f],$=Jn[g.type]?.label||g.type,U=Jn[w.type]?.label||w.type,V=Math.round(w.y-(g.y+g.height)),B=Math.round(w.x-(g.x+g.width));l+=`- ${$} \u2194 ${U}: h=\`${B}px\` v=\`${V}px\`
`}}o==="forensic"&&(l+=`
### Z-Order (placement order)
`,e.forEach((L,f)=>{let g=Jn[L.type]?.label||L.type;l+=`${f}. ${g} at \`(${Math.round(L.x)}, ${Math.round(L.y)})\`
`}))}l+=`
### Suggested Implementation
`;let a=r.some(L=>L.type==="navigation"),m=r.some(L=>L.type==="hero"),p=r.some(L=>L.type==="sidebar"),b=r.some(L=>L.type==="footer"),y=r.filter(L=>L.type==="card"),R=r.filter(L=>L.type==="form"),C=r.filter(L=>L.type==="table"),N=r.filter(L=>L.type==="modal");if(a&&(l+=`- Top navigation bar with logo + nav links + CTA
`),m&&(l+=`- Hero section with heading, subtext, and call-to-action
`),p&&(l+=`- Sidebar layout \u2014 use CSS Grid with sidebar + main content area
`),y.length>1?l+=`- ${y.length}-column card grid \u2014 use CSS Grid or Flexbox
`:y.length===1&&(l+=`- Card component with image + content area
`),R.length>0&&(l+=`- ${R.length} form${R.length>1?"s":""} \u2014 add proper labels, validation, and submit handling
`),C.length>0&&(l+=`- Data table \u2014 consider sortable columns and pagination
`),N.length>0&&(l+=`- Modal dialog \u2014 add overlay backdrop and focus trapping
`),b&&(l+=`- Multi-column footer with links
`),o==="detailed"||o==="forensic"){if(l+=`
### CSS Suggestions
`,p){let L=r.find(f=>f.type==="sidebar");l+=`- \`display: grid; grid-template-columns: ${Math.round(L.width)}px 1fr;\`
`}if(y.length>1){let L=Math.round(y[0].width);l+=`- \`display: grid; grid-template-columns: repeat(${y.length}, ${L}px); gap: 16px;\`
`}a&&(l+="- Navigation: `position: sticky; top: 0; z-index: 50;`\n")}return l}function dp(e,t="standard",n){let{sections:o}=e,r=[];for(let p of o){let b=p.originalRect,y=p.currentRect,R=Math.abs(b.x-y.x)>1||Math.abs(b.y-y.y)>1,C=Math.abs(b.width-y.width)>1||Math.abs(b.height-y.height)>1;if(!R&&!C){t==="forensic"&&r.push({section:p,posMoved:!1,sizeChanged:!1});continue}r.push({section:p,posMoved:R,sizeChanged:C})}if(r.length===0||t!=="forensic"&&r.every(p=>!p.posMoved&&!p.sizeChanged))return"";let l=`## Suggested Layout Changes

`,i=n?n.width:typeof window<"u"?window.innerWidth:0,s=n?n.height:typeof window<"u"?window.innerHeight:0,a=Kp({width:i,height:s});t!=="compact"&&(l+=Gp(a)),t==="forensic"&&(l+=`> Detected at: \`${new Date(e.detectedAt).toISOString()}\`
`,l+=`> Total sections: ${o.length}

`);let m=p=>o.map(b=>({label:b.label,selector:b.selector,rect:p==="original"?b.originalRect:b.currentRect}));l+=`**Changes:**
`;for(let{section:p,posMoved:b,sizeChanged:y}of r){let R=p.originalRect,C=p.currentRect;if(!b&&!y){l+=`- ${p.label} \u2014 unchanged at (${Math.round(C.x)}, ${Math.round(C.y)}) ${Math.round(C.width)}\xD7${Math.round(C.height)}px
`;continue}if(t==="compact"){b&&y?l+=`- Suggested: move **${p.label}** to (${Math.round(C.x)}, ${Math.round(C.y)}) ${Math.round(C.width)}\xD7${Math.round(C.height)}px
`:b?l+=`- Suggested: move **${p.label}** to (${Math.round(C.x)}, ${Math.round(C.y)})
`:l+=`- Suggested: resize **${p.label}** to ${Math.round(C.width)}\xD7${Math.round(C.height)}px
`;continue}if(b&&y?l+=`- Suggested: move and resize **${p.label}**
`:b?l+=`- Suggested: move **${p.label}**
`:l+=`- Suggested: resize **${p.label}** from ${Math.round(R.width)}\xD7${Math.round(R.height)}px to ${Math.round(C.width)}\xD7${Math.round(C.height)}px
`,b){let L=Ru(R,m("original")),f=Ru(C,m("current")),g=y?{width:R.width,height:R.height}:void 0;l+=`  - Currently ${k2(L,{x:R.x,y:R.y},g)}
`;let w=y?{width:C.width,height:C.height}:void 0,$=`at (${Math.round(C.x)}, ${Math.round(C.y)})`,U=w?`, ${Math.round(w.width)}\xD7${Math.round(w.height)}px`:"",B=Vp(f,{includeLeftRight:t==="detailed"||t==="forensic"});if(B.length>0){l+=`  - Suggested position ${$}${U}: ${B[0]}
`;for(let ye=1;ye<B.length;ye++)l+=`    ${B[ye]}
`}else l+=`  - Suggested position ${$}${U}
`;let q=qp(C,a);q&&(l+=`  - CSS: ${q}
`)}let N=M2(p.selector);if(N&&(l+=`  - ${N}
`),l+=`  - Selector: \`${p.selector}\`
`,t==="detailed"||t==="forensic"){let L=p.className?`${p.tagName}.${p.className.split(" ")[0]}`:p.tagName;L!==p.selector&&(l+=`  - Element: \`${L}\`
`),p.role&&(l+=`  - Role: \`${p.role}\`
`),t==="forensic"&&p.textSnippet&&(l+=`  - Text: "${p.textSnippet}"
`)}t==="forensic"&&(l+=`  - Original rect: \`{ x: ${Math.round(R.x)}, y: ${Math.round(R.y)}, w: ${Math.round(R.width)}, h: ${Math.round(R.height)} }\`
`,l+=`  - Current rect: \`{ x: ${Math.round(C.x)}, y: ${Math.round(C.y)}, w: ${Math.round(C.width)}, h: ${Math.round(C.height)} }\`
`)}if(t!=="compact"){let p=r.filter(y=>y.posMoved).map(y=>({label:y.section.label,originalRect:y.section.originalRect,currentRect:y.section.currentRect})),b=C2(p);if(b.length>0){l+=`
### Layout Summary
`;for(let y of b)l+=`- ${y}
`}}if(t!=="compact"&&o.length>1){l+=`
### All Sections (current positions)
`;let p=[...o].sort((b,y)=>Math.abs(b.currentRect.y-y.currentRect.y)<20?b.currentRect.x-y.currentRect.x:b.currentRect.y-y.currentRect.y);for(let b of p){let y=b.currentRect,R=Math.abs(y.x-b.originalRect.x)>1||Math.abs(y.y-b.originalRect.y)>1||Math.abs(y.width-b.originalRect.width)>1||Math.abs(y.height-b.originalRect.height)>1;l+=`- ${b.label}: \`${Math.round(y.width)}\xD7${Math.round(y.height)}px\` at \`(${Math.round(y.x)}, ${Math.round(y.y)})\`${R?" \u2190 suggested":""}
`}}return l}var Pu="feedback-annotations-",Zp=7;function Bi(e){return`${Pu}${e}`}function Pa(e){if(typeof window>"u")return[];try{let t=localStorage.getItem(Bi(e));if(!t)return[];let n=JSON.parse(t),o=Date.now()-Zp*24*60*60*1e3;return n.filter(r=>!r.timestamp||r.timestamp>o)}catch{return[]}}function zu(e,t){if(!(typeof window>"u"))try{localStorage.setItem(Bi(e),JSON.stringify(t))}catch{}}function E2(){let e=new Map;if(typeof window>"u")return e;try{let t=Date.now()-Zp*24*60*60*1e3;for(let n=0;n<localStorage.length;n++){let o=localStorage.key(n);if(o?.startsWith(Pu)){let r=o.slice(Pu.length),l=localStorage.getItem(o);if(l){let s=JSON.parse(l).filter(a=>!a.timestamp||a.timestamp>t);s.length>0&&e.set(r,s)}}}}catch{}return e}function Ni(e,t,n){let o=t.map(r=>({...r,_syncedTo:n}));zu(e,o)}var Ou="agentation-design-";function L2(e){if(typeof window>"u")return[];try{let t=localStorage.getItem(`${Ou}${e}`);return t?JSON.parse(t):[]}catch{return[]}}function I2(e,t){if(!(typeof window>"u"))try{localStorage.setItem(`${Ou}${e}`,JSON.stringify(t))}catch{}}function N2(e){if(!(typeof window>"u"))try{localStorage.removeItem(`${Ou}${e}`)}catch{}}var Au="agentation-rearrange-";function $2(e){if(typeof window>"u")return null;try{let t=localStorage.getItem(`${Au}${e}`);return t?JSON.parse(t):null}catch{return null}}function R2(e,t){if(!(typeof window>"u"))try{localStorage.setItem(`${Au}${e}`,JSON.stringify(t))}catch{}}function P2(e){if(!(typeof window>"u"))try{localStorage.removeItem(`${Au}${e}`)}catch{}}var Wu="agentation-wireframe-";function T2(e){if(typeof window>"u")return null;try{let t=localStorage.getItem(`${Wu}${e}`);return t?JSON.parse(t):null}catch{return null}}function up(e,t){if(!(typeof window>"u"))try{localStorage.setItem(`${Wu}${e}`,JSON.stringify(t))}catch{}}function Ia(e){if(!(typeof window>"u"))try{localStorage.removeItem(`${Wu}${e}`)}catch{}}var Jp="agentation-session-";function Fu(e){return`${Jp}${e}`}function D2(e){if(typeof window>"u")return null;try{return localStorage.getItem(Fu(e))}catch{return null}}function vu(e,t){if(!(typeof window>"u"))try{localStorage.setItem(Fu(e),t)}catch{}}function B2(e){if(!(typeof window>"u"))try{localStorage.removeItem(Fu(e))}catch{}}var Tu=`${Jp}toolbar-hidden`;function z2(){if(typeof window>"u")return!1;try{return sessionStorage.getItem(Tu)==="1"}catch{return!1}}function O2(e){if(!(typeof window>"u"))try{e?sessionStorage.setItem(Tu,"1"):sessionStorage.removeItem(Tu)}catch{}}async function wu(e,t){let n=await fetch(`${e}/sessions`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:t})});if(!n.ok)throw new Error(`Failed to create session: ${n.status}`);return n.json()}async function _p(e,t){let n=await fetch(`${e}/sessions/${t}`);if(!n.ok)throw new Error(`Failed to get session: ${n.status}`);return n.json()}async function xl(e,t,n){let o=await fetch(`${e}/sessions/${t}/annotations`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!o.ok)throw new Error(`Failed to sync annotation: ${o.status}`);return o.json()}async function fp(e,t,n){let o=await fetch(`${e}/annotations/${t}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!o.ok)throw new Error(`Failed to update annotation: ${o.status}`);return o.json()}async function or(e,t){let n=await fetch(`${e}/annotations/${t}`,{method:"DELETE"});if(!n.ok)throw new Error(`Failed to delete annotation: ${n.status}`)}var et={FunctionComponent:0,ClassComponent:1,IndeterminateComponent:2,HostRoot:3,HostPortal:4,HostComponent:5,HostText:6,Fragment:7,Mode:8,ContextConsumer:9,ContextProvider:10,ForwardRef:11,Profiler:12,SuspenseComponent:13,MemoComponent:14,SimpleMemoComponent:15,LazyComponent:16,IncompleteClassComponent:17,DehydratedFragment:18,SuspenseListComponent:19,ScopeComponent:21,OffscreenComponent:22,LegacyHiddenComponent:23,CacheComponent:24,TracingMarkerComponent:25,HostHoistable:26,HostSingleton:27,IncompleteFunctionComponent:28,Throw:29,ViewTransitionComponent:30,ActivityComponent:31},hp=new Set(["Component","PureComponent","Fragment","Suspense","Profiler","StrictMode","Routes","Route","Outlet","Root","ErrorBoundaryHandler","HotReload","Hot"]),pp=[/Boundary$/,/BoundaryHandler$/,/Provider$/,/Consumer$/,/^(Inner|Outer)/,/Router$/,/^Client(Page|Segment|Root)/,/^Segment(ViewNode|Node)$/,/^LayoutSegment/,/^Server(Root|Component|Render)/,/^RSC/,/Context$/,/^Hot(Reload)?$/,/^(Dev|React)(Overlay|Tools|Root)/,/Overlay$/,/Handler$/,/^With[A-Z]/,/Wrapper$/,/^Root$/],A2=[/Page$/,/View$/,/Screen$/,/Section$/,/Card$/,/List$/,/Item$/,/Form$/,/Modal$/,/Dialog$/,/Button$/,/Nav$/,/Header$/,/Footer$/,/Layout$/,/Panel$/,/Tab$/,/Menu$/];function W2(e){let t=e?.mode??"filtered",n=hp;if(e?.skipExact){let o=e.skipExact instanceof Set?e.skipExact:new Set(e.skipExact);n=new Set([...hp,...o])}return{maxComponents:e?.maxComponents??6,maxDepth:e?.maxDepth??30,mode:t,skipExact:n,skipPatterns:e?.skipPatterns?[...pp,...e.skipPatterns]:pp,userPatterns:e?.userPatterns??A2,filter:e?.filter}}function F2(e){return e.replace(/([a-z])([A-Z])/g,"$1-$2").replace(/([A-Z])([A-Z][a-z])/g,"$1-$2").toLowerCase()}function j2(e,t=10){let n=new Set,o=e,r=0;for(;o&&r<t;)o.className&&typeof o.className=="string"&&o.className.split(/\s+/).forEach(l=>{if(l.length>1){let i=l.replace(/[_][a-zA-Z0-9]{5,}.*$/,"").toLowerCase();i.length>1&&n.add(i)}}),o=o.parentElement,r++;return n}function H2(e,t){let n=F2(e);for(let o of t){if(o===n)return!0;let r=n.split("-").filter(i=>i.length>2),l=o.split("-").filter(i=>i.length>2);for(let i of r)for(let s of l)if(i===s||i.includes(s)||s.includes(i))return!0}return!1}function U2(e,t,n,o){if(n.filter)return n.filter(e,t);switch(n.mode){case"all":return!0;case"filtered":return!(n.skipExact.has(e)||n.skipPatterns.some(r=>r.test(e)));case"smart":return n.skipExact.has(e)||n.skipPatterns.some(r=>r.test(e))?!1:!!(o&&H2(e,o)||n.userPatterns.some(r=>r.test(e)));default:return!0}}var vl=null,Y2=new WeakMap;function bu(e){return Object.keys(e).some(t=>t.startsWith("__reactFiber$")||t.startsWith("__reactInternalInstance$")||t.startsWith("__reactProps$"))}function X2(){if(vl!==null)return vl;if(typeof document>"u")return!1;if(document.body&&bu(document.body))return vl=!0,!0;let e=["#root","#app","#__next","[data-reactroot]"];for(let t of e){let n=document.querySelector(t);if(n&&bu(n))return vl=!0,!0}if(document.body){for(let t of document.body.children)if(bu(t))return vl=!0,!0}return vl=!1,!1}var $i={map:Y2};function Q2(e){return Object.keys(e).find(n=>n.startsWith("__reactFiber$")||n.startsWith("__reactInternalInstance$"))||null}function V2(e){let t=Q2(e);return t?e[t]:null}function Er(e){return e?e.displayName?e.displayName:e.name?e.name:null:null}function K2(e){let{tag:t,type:n,elementType:o}=e;if(t===et.HostComponent||t===et.HostText||t===et.HostHoistable||t===et.HostSingleton||t===et.Fragment||t===et.Mode||t===et.Profiler||t===et.DehydratedFragment||t===et.HostRoot||t===et.HostPortal||t===et.ScopeComponent||t===et.OffscreenComponent||t===et.LegacyHiddenComponent||t===et.CacheComponent||t===et.TracingMarkerComponent||t===et.Throw||t===et.ViewTransitionComponent||t===et.ActivityComponent)return null;if(t===et.ForwardRef){let r=o;if(r?.render){let l=Er(r.render);if(l)return l}return r?.displayName?r.displayName:Er(n)}if(t===et.MemoComponent||t===et.SimpleMemoComponent){let r=o;if(r?.type){let l=Er(r.type);if(l)return l}return r?.displayName?r.displayName:Er(n)}if(t===et.ContextProvider){let r=n;return r?._context?.displayName?`${r._context.displayName}.Provider`:null}if(t===et.ContextConsumer){let r=n;return r?.displayName?`${r.displayName}.Consumer`:null}if(t===et.LazyComponent){let r=o;return r?._status===1&&r._result?Er(r._result):null}return t===et.SuspenseComponent||t===et.SuspenseListComponent?null:t===et.IncompleteClassComponent||t===et.IncompleteFunctionComponent||t===et.FunctionComponent||t===et.ClassComponent||t===et.IndeterminateComponent?Er(n):null}function q2(e){return e.length<=2||e.length<=3&&e===e.toLowerCase()}function G2(e,t){let n=W2(t),o=n.mode==="all";if(o){let a=$i.map.get(e);if(a!==void 0)return a}if(!X2()){let a={path:null,components:[]};return o&&$i.map.set(e,a),a}let r=n.mode==="smart"?j2(e):void 0,l=[];try{let a=V2(e),m=0;for(;a&&m<n.maxDepth&&l.length<n.maxComponents;){let p=K2(a);p&&!q2(p)&&U2(p,m,n,r)&&l.push(p),a=a.return,m++}}catch{let a={path:null,components:[]};return o&&$i.map.set(e,a),a}if(l.length===0){let a={path:null,components:[]};return o&&$i.map.set(e,a),a}let s={path:l.slice().reverse().map(a=>`<${a}>`).join(" "),components:l};return o&&$i.map.set(e,s),s}var Ri={FunctionComponent:0,ClassComponent:1,IndeterminateComponent:2,HostRoot:3,HostPortal:4,HostComponent:5,HostText:6,Fragment:7,Mode:8,ContextConsumer:9,ContextProvider:10,ForwardRef:11,Profiler:12,SuspenseComponent:13,MemoComponent:14,SimpleMemoComponent:15,LazyComponent:16};function Z2(e){if(!e||typeof e!="object")return null;let t=Object.keys(e),n=t.find(l=>l.startsWith("__reactFiber$"));if(n)return e[n]||null;let o=t.find(l=>l.startsWith("__reactInternalInstance$"));if(o)return e[o]||null;let r=t.find(l=>{if(!l.startsWith("__react"))return!1;let i=e[l];return i&&typeof i=="object"&&"_debugSource"in i});return r&&e[r]||null}function zi(e){if(!e.type||typeof e.type=="string")return null;if(typeof e.type=="object"||typeof e.type=="function"){let t=e.type;if(t.displayName)return t.displayName;if(t.name)return t.name}return null}function J2(e,t=50){let n=e,o=0;for(;n&&o<t;){if(n._debugSource)return{source:n._debugSource,componentName:zi(n)};if(n._debugOwner?._debugSource)return{source:n._debugOwner._debugSource,componentName:zi(n._debugOwner)};n=n.return,o++}return null}function ex(e){let t=e,n=0,o=50;for(;t&&n<o;){let r=t,l=["_debugSource","__source","_source","debugSource"];for(let i of l){let s=r[i];if(s&&typeof s=="object"&&"fileName"in s)return{source:s,componentName:zi(t)}}if(t.memoizedProps){let i=t.memoizedProps;if(i.__source&&typeof i.__source=="object"){let s=i.__source;if(s.fileName&&s.lineNumber)return{source:{fileName:s.fileName,lineNumber:s.lineNumber,columnNumber:s.columnNumber},componentName:zi(t)}}}t=t.return,n++}return null}var Na=new Map;function tx(e){let t=e.tag,n=e.type,o=e.elementType;if(typeof n=="string"||n==null||typeof n=="function"&&n.prototype?.isReactComponent)return null;if((t===Ri.FunctionComponent||t===Ri.IndeterminateComponent)&&typeof n=="function")return n;if(t===Ri.ForwardRef&&o){let r=o.render;if(typeof r=="function")return r}if((t===Ri.MemoComponent||t===Ri.SimpleMemoComponent)&&o){let r=o.type;if(typeof r=="function")return r}return typeof n=="function"?n:null}function nx(){let e=em.default,t=e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;if(t&&"H"in t)return{get:()=>t.H,set:o=>{t.H=o}};let n=e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;if(n){let o=n.ReactCurrentDispatcher;if(o&&"current"in o)return{get:()=>o.current,set:r=>{o.current=r}}}return null}function ox(e){let t=e.split(`
`),n=[/source-location/,/\/dist\/index\./,/node_modules\//,/react-dom/,/react\.development/,/react\.production/,/chunk-[A-Z0-9]+/i,/react-stack-bottom-frame/,/react-reconciler/,/scheduler/,/<anonymous>/],o=/^\s*at\s+(?:.*?\s+\()?(.+?):(\d+):(\d+)\)?$/,r=/^[^@]*@(.+?):(\d+):(\d+)$/;for(let l of t){let i=l.trim();if(!i||n.some(a=>a.test(i)))continue;let s=o.exec(i)||r.exec(i);if(s)return{fileName:s[1],line:parseInt(s[2],10),column:parseInt(s[3],10)}}return null}function rx(e){let t=e;return t=t.replace(/[?#].*$/,""),t=t.replace(/^turbopack:\/\/\/\[project\]\//,""),t=t.replace(/^webpack-internal:\/\/\/\.\//,""),t=t.replace(/^webpack-internal:\/\/\//,""),t=t.replace(/^webpack:\/\/\/\.\//,""),t=t.replace(/^webpack:\/\/\//,""),t=t.replace(/^turbopack:\/\/\//,""),t=t.replace(/^https?:\/\/[^/]+\//,""),t=t.replace(/^file:\/\/\//,"/"),t=t.replace(/^\([^)]+\)\/\.\//,""),t=t.replace(/^\.\//,""),t}function lx(e){let t=tx(e);if(!t)return null;if(Na.has(t))return Na.get(t);let n=nx();if(!n)return Na.set(t,null),null;let o=n.get(),r=null;try{let l=new Proxy({},{get(){throw new Error("probe")}});n.set(l);try{t({})}catch(i){if(i instanceof Error&&i.message==="probe"&&i.stack){let s=ox(i.stack);s&&(r={fileName:rx(s.fileName),lineNumber:s.line,columnNumber:s.column,componentName:zi(e)||void 0})}}}finally{n.set(o)}return Na.set(t,r),r}function ix(e,t=15){let n=e,o=0;for(;n&&o<t;){let r=lx(n);if(r)return r;n=n.return,o++}return null}function Du(e){let t=Z2(e);if(!t)return{found:!1,reason:"no-fiber",isReactApp:!1,isProduction:!1};let n=J2(t);if(n||(n=ex(t)),n?.source)return{found:!0,source:{fileName:n.source.fileName,lineNumber:n.source.lineNumber,columnNumber:n.source.columnNumber,componentName:n.componentName||void 0},isReactApp:!0,isProduction:!1};let o=ix(t);return o?{found:!0,source:o,isReactApp:!0,isProduction:!1}:{found:!1,reason:"no-debug-source",isReactApp:!0,isProduction:!1}}function sx(e,t="path"){let{fileName:n,lineNumber:o,columnNumber:r}=e,l=`${n}:${o}`;return r!==void 0&&(l+=`:${r}`),t==="vscode"?`vscode://file${n.startsWith("/")?"":"/"}${l}`:l}function ax(e,t=10){let n=e,o=0;for(;n&&o<t;){let r=Du(n);if(r.found)return r;n=n.parentElement,o++}return Du(e)}var cx=`.styles-module__toolbar___wNsdK svg[fill=none],
.styles-module__markersLayer___-25j1 svg[fill=none],
.styles-module__fixedMarkersLayer___ffyX6 svg[fill=none] {
  fill: none !important;
}
.styles-module__toolbar___wNsdK svg[fill=none] :not([fill]),
.styles-module__markersLayer___-25j1 svg[fill=none] :not([fill]),
.styles-module__fixedMarkersLayer___ffyX6 svg[fill=none] :not([fill]) {
  fill: none !important;
}

.styles-module__controlsContent___9GJWU :where(button, input, select, textarea, label) {
  background: unset;
  border: unset;
  border-radius: unset;
  padding: unset;
  margin: unset;
  color: unset;
  font-family: unset;
  font-weight: unset;
  font-style: unset;
  line-height: unset;
  letter-spacing: unset;
  text-transform: unset;
  text-decoration: unset;
  box-shadow: unset;
  outline: unset;
}

@keyframes styles-module__toolbarEnter___u8RRu {
  from {
    opacity: 0;
    transform: scale(0.5) rotate(90deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}
@keyframes styles-module__toolbarHide___y8kaT {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.8);
  }
}
@keyframes styles-module__badgeEnter___mVQLj {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__scaleIn___c-r1K {
  from {
    opacity: 0;
    transform: scale(0.85);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__scaleOut___Wctwz {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.85);
  }
}
@keyframes styles-module__slideUp___kgD36 {
  from {
    opacity: 0;
    transform: scale(0.85) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
@keyframes styles-module__slideDown___zcdje {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.85) translateY(8px);
  }
}
@keyframes styles-module__fadeIn___b9qmf {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes styles-module__fadeOut___6Ut6- {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
@keyframes styles-module__hoverHighlightIn___6WYHY {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__hoverTooltipIn___FYGQx {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.styles-module__disableTransitions___EopxO :is(*, *::before, *::after) {
  transition: none !important;
}

.styles-module__toolbar___wNsdK {
  position: fixed;
  bottom: 1.25rem;
  right: 1.25rem;
  width: 337px;
  z-index: 100000;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  pointer-events: none;
  transition: left 0s, top 0s, right 0s, bottom 0s;
}

:where(.styles-module__toolbar___wNsdK) {
  bottom: 1.25rem;
  right: 1.25rem;
}

.styles-module__toolbarContainer___dIhma {
  position: relative;
  user-select: none;
  margin-left: auto;
  align-self: flex-end;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  color: #fff;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), 0 4px 16px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
  transition: width 0.4s cubic-bezier(0.19, 1, 0.22, 1), transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
}
.styles-module__toolbarContainer___dIhma.styles-module__entrance___sgHd8 {
  animation: styles-module__toolbarEnter___u8RRu 0.5s cubic-bezier(0.34, 1.2, 0.64, 1) forwards;
}
.styles-module__toolbarContainer___dIhma.styles-module__hiding___1td44 {
  animation: styles-module__toolbarHide___y8kaT 0.4s cubic-bezier(0.4, 0, 1, 1) forwards;
  pointer-events: none;
}
.styles-module__toolbarContainer___dIhma.styles-module__collapsed___Rydsn {
  width: 44px;
  height: 44px;
  border-radius: 22px;
  padding: 0;
  cursor: pointer;
}
.styles-module__toolbarContainer___dIhma.styles-module__collapsed___Rydsn svg {
  margin-top: -1px;
}
.styles-module__toolbarContainer___dIhma.styles-module__collapsed___Rydsn:hover {
  background: #2a2a2a;
}
.styles-module__toolbarContainer___dIhma.styles-module__collapsed___Rydsn:active {
  transform: scale(0.95);
}
.styles-module__toolbarContainer___dIhma.styles-module__expanded___ofKPx {
  height: 44px;
  border-radius: 1.5rem;
  padding: 0.375rem;
  width: 297px;
}
.styles-module__toolbarContainer___dIhma.styles-module__expanded___ofKPx.styles-module__serverConnected___Gfbou {
  width: 337px;
}

.styles-module__toggleContent___0yfyP {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.1s cubic-bezier(0.19, 1, 0.22, 1);
}
.styles-module__toggleContent___0yfyP.styles-module__visible___KHwEW {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}
.styles-module__toggleContent___0yfyP.styles-module__hidden___Ae8H4 {
  opacity: 0;
  pointer-events: none;
}

.styles-module__controlsContent___9GJWU {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  transition: filter 0.8s cubic-bezier(0.19, 1, 0.22, 1), opacity 0.8s cubic-bezier(0.19, 1, 0.22, 1), transform 0.6s cubic-bezier(0.19, 1, 0.22, 1);
}
.styles-module__controlsContent___9GJWU.styles-module__visible___KHwEW {
  opacity: 1;
  filter: blur(0px);
  transform: scale(1);
  visibility: visible;
  pointer-events: auto;
}
.styles-module__controlsContent___9GJWU.styles-module__hidden___Ae8H4 {
  pointer-events: none;
  opacity: 0;
  filter: blur(10px);
  transform: scale(0.4);
}

.styles-module__badge___2XsgF {
  position: absolute;
  top: -13px;
  right: -13px;
  user-select: none;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background-color: var(--agentation-color-accent);
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  opacity: 1;
  transition: transform 0.3s ease, opacity 0.2s ease;
  transform: scale(1);
}
.styles-module__badge___2XsgF.styles-module__fadeOut___6Ut6- {
  opacity: 0;
  transform: scale(0);
  pointer-events: none;
}
.styles-module__badge___2XsgF.styles-module__entrance___sgHd8 {
  animation: styles-module__badgeEnter___mVQLj 0.3s cubic-bezier(0.34, 1.2, 0.64, 1) 0.4s both;
}

.styles-module__controlButton___8Q0jc {
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease, opacity 0.2s ease;
}
.styles-module__controlButton___8Q0jc:hover:not(:disabled):not([data-active=true]):not([data-failed=true]):not([data-auto-sync=true]):not([data-error=true]):not([data-no-hover=true]) {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}
.styles-module__controlButton___8Q0jc:active:not(:disabled) {
  transform: scale(0.92);
}
.styles-module__controlButton___8Q0jc:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.styles-module__controlButton___8Q0jc[data-active=true] {
  color: var(--agentation-color-blue);
  background-color: color-mix(in srgb, var(--agentation-color-blue) 25%, transparent);
}
.styles-module__controlButton___8Q0jc[data-error=true] {
  color: var(--agentation-color-red);
  background-color: color-mix(in srgb, var(--agentation-color-red) 25%, transparent);
}
.styles-module__controlButton___8Q0jc[data-danger]:hover:not(:disabled):not([data-active=true]):not([data-failed=true]) {
  background-color: color-mix(in srgb, var(--agentation-color-red) 25%, transparent);
  color: var(--agentation-color-red);
}
.styles-module__controlButton___8Q0jc[data-no-hover=true], .styles-module__controlButton___8Q0jc.styles-module__statusShowing___te6iu {
  cursor: default;
  pointer-events: none;
  background: transparent !important;
}
.styles-module__controlButton___8Q0jc[data-auto-sync=true] {
  color: var(--agentation-color-green);
  background: transparent;
  cursor: default;
}
.styles-module__controlButton___8Q0jc[data-failed=true] {
  color: var(--agentation-color-red);
  background-color: color-mix(in srgb, var(--agentation-color-red) 25%, transparent);
}

.styles-module__buttonBadge___NeFWb {
  position: absolute;
  top: 0px;
  right: 0px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background-color: var(--agentation-color-accent);
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px #1a1a1a, 0 1px 3px rgba(0, 0, 0, 0.2);
  pointer-events: none;
}
[data-agentation-theme=light] .styles-module__buttonBadge___NeFWb {
  box-shadow: 0 0 0 2px #fff, 0 1px 3px rgba(0, 0, 0, 0.2);
}

@keyframes styles-module__mcpIndicatorPulseConnected___EDodZ {
  0%, 100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-green) 50%, transparent);
  }
  50% {
    box-shadow: 0 0 0 5px color-mix(in srgb, var(--agentation-color-green) 0%, transparent);
  }
}
@keyframes styles-module__mcpIndicatorPulseConnecting___cCYte {
  0%, 100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-yellow) 50%, transparent);
  }
  50% {
    box-shadow: 0 0 0 5px color-mix(in srgb, var(--agentation-color-yellow) 0%, transparent);
  }
}
.styles-module__mcpIndicator___zGJeL {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  pointer-events: none;
  transition: background-color 0.3s ease, opacity 0.15s ease, transform 0.15s ease;
  opacity: 1;
  transform: scale(1);
}
.styles-module__mcpIndicator___zGJeL.styles-module__connected___7c28g {
  background-color: var(--agentation-color-green);
  animation: styles-module__mcpIndicatorPulseConnected___EDodZ 2.5s ease-in-out infinite;
}
.styles-module__mcpIndicator___zGJeL.styles-module__connecting___uo-CW {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__mcpIndicatorPulseConnecting___cCYte 1.5s ease-in-out infinite;
}
.styles-module__mcpIndicator___zGJeL.styles-module__hidden___Ae8H4 {
  opacity: 0;
  transform: scale(0);
  animation: none;
}

@keyframes styles-module__connectionPulse___-Zycw {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(0.9);
  }
}
.styles-module__connectionIndicatorWrapper___L-e-3 {
  width: 8px;
  height: 34px;
  margin-left: 6px;
  margin-right: 6px;
}

.styles-module__connectionIndicator___afk9p {
  position: relative;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease, background-color 0.3s ease;
  cursor: default;
}

.styles-module__connectionIndicatorVisible___C-i5B {
  opacity: 1;
}

.styles-module__connectionIndicatorConnected___IY8pR {
  background-color: var(--agentation-color-green);
  animation: styles-module__connectionPulse___-Zycw 2.5s ease-in-out infinite;
}

.styles-module__connectionIndicatorDisconnected___kmpaZ {
  background-color: var(--agentation-color-red);
  animation: none;
}

.styles-module__connectionIndicatorConnecting___QmSLH {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__connectionPulse___-Zycw 1s ease-in-out infinite;
}

.styles-module__buttonWrapper___rBcdv {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.styles-module__buttonWrapper___rBcdv:hover .styles-module__buttonTooltip___Burd9 {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) scale(1);
  transition-delay: 0.85s;
}
.styles-module__buttonWrapper___rBcdv:has(.styles-module__controlButton___8Q0jc:disabled):hover .styles-module__buttonTooltip___Burd9 {
  opacity: 0;
  visibility: hidden;
}

.styles-module__tooltipsInSession___-0lHH .styles-module__buttonWrapper___rBcdv:hover .styles-module__buttonTooltip___Burd9 {
  transition-delay: 0s;
}

.styles-module__sendButtonWrapper___UUxG6 {
  width: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  margin-left: -0.375rem;
  transition: width 0.4s cubic-bezier(0.19, 1, 0.22, 1), opacity 0.3s cubic-bezier(0.19, 1, 0.22, 1), margin 0.4s cubic-bezier(0.19, 1, 0.22, 1);
}
.styles-module__sendButtonWrapper___UUxG6 .styles-module__controlButton___8Q0jc {
  transform: scale(0.8);
  transition: transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
}
.styles-module__sendButtonWrapper___UUxG6.styles-module__sendButtonVisible___WPSQU {
  width: 34px;
  opacity: 1;
  overflow: visible;
  pointer-events: auto;
  margin-left: 0;
}
.styles-module__sendButtonWrapper___UUxG6.styles-module__sendButtonVisible___WPSQU .styles-module__controlButton___8Q0jc {
  transform: scale(1);
}

.styles-module__buttonTooltip___Burd9 {
  position: absolute;
  bottom: calc(100% + 14px);
  left: 50%;
  transform: translateX(-50%) scale(0.95);
  padding: 6px 10px;
  background: #1a1a1a;
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 500;
  border-radius: 8px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  z-index: 100001;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: opacity 0.135s ease, transform 0.135s ease, visibility 0.135s ease;
}
.styles-module__buttonTooltip___Burd9::after {
  content: "";
  position: absolute;
  top: calc(100% - 4px);
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: #1a1a1a;
  border-radius: 0 0 2px 0;
}

.styles-module__shortcut___lEAQk {
  margin-left: 4px;
  opacity: 0.5;
}

.styles-module__tooltipBelow___m6ats .styles-module__buttonTooltip___Burd9 {
  bottom: auto;
  top: calc(100% + 14px);
  transform: translateX(-50%) scale(0.95);
}
.styles-module__tooltipBelow___m6ats .styles-module__buttonTooltip___Burd9::after {
  top: -4px;
  bottom: auto;
  border-radius: 2px 0 0 0;
}

.styles-module__tooltipBelow___m6ats .styles-module__buttonWrapper___rBcdv:hover .styles-module__buttonTooltip___Burd9 {
  transform: translateX(-50%) scale(1);
}

.styles-module__tooltipsHidden___VtLJG .styles-module__buttonTooltip___Burd9 {
  opacity: 0 !important;
  visibility: hidden !important;
  transition: none !important;
}

.styles-module__tooltipVisible___0jcCv,
.styles-module__tooltipsHidden___VtLJG .styles-module__tooltipVisible___0jcCv {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateX(-50%) scale(1) !important;
  transition-delay: 0s !important;
}

.styles-module__buttonWrapperAlignLeft___myzIp .styles-module__buttonTooltip___Burd9 {
  left: 50%;
  transform: translateX(-12px) scale(0.95);
}
.styles-module__buttonWrapperAlignLeft___myzIp .styles-module__buttonTooltip___Burd9::after {
  left: 16px;
}
.styles-module__buttonWrapperAlignLeft___myzIp:hover .styles-module__buttonTooltip___Burd9 {
  transform: translateX(-12px) scale(1);
}

.styles-module__tooltipBelow___m6ats .styles-module__buttonWrapperAlignLeft___myzIp .styles-module__buttonTooltip___Burd9 {
  transform: translateX(-12px) scale(0.95);
}
.styles-module__tooltipBelow___m6ats .styles-module__buttonWrapperAlignLeft___myzIp:hover .styles-module__buttonTooltip___Burd9 {
  transform: translateX(-12px) scale(1);
}

.styles-module__buttonWrapperAlignRight___HCQFR .styles-module__buttonTooltip___Burd9 {
  left: 50%;
  transform: translateX(calc(-100% + 12px)) scale(0.95);
}
.styles-module__buttonWrapperAlignRight___HCQFR .styles-module__buttonTooltip___Burd9::after {
  left: auto;
  right: 8px;
}
.styles-module__buttonWrapperAlignRight___HCQFR:hover .styles-module__buttonTooltip___Burd9 {
  transform: translateX(calc(-100% + 12px)) scale(1);
}

.styles-module__tooltipBelow___m6ats .styles-module__buttonWrapperAlignRight___HCQFR .styles-module__buttonTooltip___Burd9 {
  transform: translateX(calc(-100% + 12px)) scale(0.95);
}
.styles-module__tooltipBelow___m6ats .styles-module__buttonWrapperAlignRight___HCQFR:hover .styles-module__buttonTooltip___Burd9 {
  transform: translateX(calc(-100% + 12px)) scale(1);
}

.styles-module__divider___c--s1 {
  width: 1px;
  height: 12px;
  background: rgba(255, 255, 255, 0.15);
  margin: 0 0.125rem;
}

.styles-module__overlay___Q1O9y {
  position: fixed;
  inset: 0;
  z-index: 99997;
  pointer-events: none;
}
.styles-module__overlay___Q1O9y > * {
  pointer-events: auto;
}

.styles-module__hoverHighlight___ogakW {
  position: fixed;
  border: 2px solid color-mix(in srgb, var(--agentation-color-accent) 50%, transparent);
  border-radius: 4px;
  background-color: color-mix(in srgb, var(--agentation-color-accent) 4%, transparent);
  pointer-events: none !important;
  box-sizing: border-box;
  will-change: opacity;
  contain: layout style;
}
.styles-module__hoverHighlight___ogakW.styles-module__enter___WFIki {
  animation: styles-module__hoverHighlightIn___6WYHY 0.12s ease-out forwards;
}

.styles-module__multiSelectOutline___cSJ-m {
  position: fixed;
  border: 2px dashed color-mix(in srgb, var(--agentation-color-green) 60%, transparent);
  border-radius: 4px;
  pointer-events: none !important;
  background-color: color-mix(in srgb, var(--agentation-color-green) 5%, transparent);
  box-sizing: border-box;
  will-change: opacity;
}
.styles-module__multiSelectOutline___cSJ-m.styles-module__enter___WFIki {
  animation: styles-module__fadeIn___b9qmf 0.15s ease-out forwards;
}
.styles-module__multiSelectOutline___cSJ-m.styles-module__exit___fyOJ0 {
  animation: styles-module__fadeOut___6Ut6- 0.15s ease-out forwards;
}

.styles-module__singleSelectOutline___QhX-O {
  position: fixed;
  border: 2px solid color-mix(in srgb, var(--agentation-color-blue) 60%, transparent);
  border-radius: 4px;
  pointer-events: none !important;
  background-color: color-mix(in srgb, var(--agentation-color-blue) 5%, transparent);
  box-sizing: border-box;
  will-change: opacity;
}
.styles-module__singleSelectOutline___QhX-O.styles-module__enter___WFIki {
  animation: styles-module__fadeIn___b9qmf 0.15s ease-out forwards;
}
.styles-module__singleSelectOutline___QhX-O.styles-module__exit___fyOJ0 {
  animation: styles-module__fadeOut___6Ut6- 0.15s ease-out forwards;
}

.styles-module__hoverTooltip___bvLk7 {
  position: fixed;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #fff;
  background: rgba(0, 0, 0, 0.85);
  padding: 0.35rem 0.6rem;
  border-radius: 0.375rem;
  pointer-events: none !important;
  white-space: nowrap;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.styles-module__hoverTooltip___bvLk7.styles-module__enter___WFIki {
  animation: styles-module__hoverTooltipIn___FYGQx 0.1s ease-out forwards;
}

.styles-module__hoverReactPath___gx1IJ {
  font-size: 0.625rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.15rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.styles-module__hoverElementName___QMLMl {
  overflow: hidden;
  text-overflow: ellipsis;
}

.styles-module__markersLayer___-25j1 {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0;
  z-index: 99998;
  pointer-events: none;
}
.styles-module__markersLayer___-25j1 > * {
  pointer-events: auto;
}

.styles-module__fixedMarkersLayer___ffyX6 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99998;
  pointer-events: none;
}
.styles-module__fixedMarkersLayer___ffyX6 > * {
  pointer-events: auto;
}

.styles-module__marker___6sQrs {
  position: absolute;
  width: 22px;
  height: 22px;
  background: var(--agentation-color-blue);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 600;
  transform: translate(-50%, -50%) scale(1);
  opacity: 1;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2), inset 0 0 0 1px rgba(0, 0, 0, 0.04);
  user-select: none;
  will-change: transform, opacity;
  contain: layout style;
  z-index: 1;
}
.styles-module__marker___6sQrs:hover {
  z-index: 2;
}
.styles-module__marker___6sQrs:not(.styles-module__enter___WFIki):not(.styles-module__exit___fyOJ0):not(.styles-module__clearing___FQ--7) {
  transition: background-color 0.15s ease, transform 0.1s ease;
}
.styles-module__marker___6sQrs.styles-module__enter___WFIki {
  animation: styles-module__markerIn___5FaAP 0.25s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.styles-module__marker___6sQrs.styles-module__exit___fyOJ0 {
  animation: styles-module__markerOut___GU5jX 0.2s ease-out both;
  pointer-events: none;
}
.styles-module__marker___6sQrs.styles-module__clearing___FQ--7 {
  animation: styles-module__markerOut___GU5jX 0.15s ease-out both;
  pointer-events: none;
}
.styles-module__marker___6sQrs:not(.styles-module__enter___WFIki):not(.styles-module__exit___fyOJ0):not(.styles-module__clearing___FQ--7):hover {
  transform: translate(-50%, -50%) scale(1.1);
}
.styles-module__marker___6sQrs.styles-module__pending___2IHLC {
  position: fixed;
  background-color: var(--agentation-color-blue);
  cursor: default;
}
.styles-module__marker___6sQrs.styles-module__fixed___dBMHC {
  position: fixed;
}
.styles-module__marker___6sQrs.styles-module__multiSelect___YWiuz {
  background-color: var(--agentation-color-green);
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-size: 0.75rem;
}
.styles-module__marker___6sQrs.styles-module__multiSelect___YWiuz.styles-module__pending___2IHLC {
  background-color: var(--agentation-color-green);
}
.styles-module__marker___6sQrs.styles-module__hovered___ZgXIy {
  background-color: var(--agentation-color-red);
}

.styles-module__renumber___nCTxD {
  display: block;
  animation: styles-module__renumberRoll___Wgbq3 0.2s ease-out;
}

@keyframes styles-module__renumberRoll___Wgbq3 {
  0% {
    transform: translateX(-40%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}
.styles-module__markerTooltip___aLJID {
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%) scale(0.909);
  z-index: 100002;
  background: #1a1a1a;
  padding: 8px 0.75rem;
  border-radius: 0.75rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-weight: 400;
  color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08);
  min-width: 120px;
  max-width: 200px;
  pointer-events: none;
  cursor: default;
}
.styles-module__markerTooltip___aLJID.styles-module__enter___WFIki {
  animation: styles-module__tooltipIn___0N31w 0.1s ease-out forwards;
}

.styles-module__markerQuote___FHmrz {
  display: block;
  font-size: 12px;
  font-style: italic;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.3125rem;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.styles-module__markerNote___QkrrS {
  display: block;
  font-size: 13px;
  font-weight: 400;
  line-height: 1.4;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-bottom: 2px;
}

.styles-module__markerHint___2iF-6 {
  display: block;
  font-size: 0.625rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 0.375rem;
  white-space: nowrap;
}

.styles-module__settingsPanel___OxX3Y {
  position: absolute;
  right: 5px;
  bottom: calc(100% + 0.5rem);
  z-index: 1;
  overflow: hidden;
  background: #1c1c1c;
  border-radius: 1rem;
  padding: 13px 0 16px;
  min-width: 205px;
  cursor: default;
  opacity: 1;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.04);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.styles-module__settingsPanel___OxX3Y::before, .styles-module__settingsPanel___OxX3Y::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 16px;
  z-index: 2;
  pointer-events: none;
}
.styles-module__settingsPanel___OxX3Y::before {
  left: 0;
  background: linear-gradient(to right, #1c1c1c 0%, transparent 100%);
}
.styles-module__settingsPanel___OxX3Y::after {
  right: 0;
  background: linear-gradient(to left, #1c1c1c 0%, transparent 100%);
}
.styles-module__settingsPanel___OxX3Y .styles-module__settingsHeader___pwDY9,
.styles-module__settingsPanel___OxX3Y .styles-module__settingsBrand___0gJeM,
.styles-module__settingsPanel___OxX3Y .styles-module__settingsBrandSlash___uTG18,
.styles-module__settingsPanel___OxX3Y .styles-module__settingsVersion___TUcFq,
.styles-module__settingsPanel___OxX3Y .styles-module__settingsSection___m-YM2,
.styles-module__settingsPanel___OxX3Y .styles-module__settingsLabel___8UjfX,
.styles-module__settingsPanel___OxX3Y .styles-module__cycleButton___FMKfw,
.styles-module__settingsPanel___OxX3Y .styles-module__cycleDot___nPgLY,
.styles-module__settingsPanel___OxX3Y .styles-module__dropdownButton___16NPz,
.styles-module__settingsPanel___OxX3Y .styles-module__toggleLabel___Xm8Aa,
.styles-module__settingsPanel___OxX3Y .styles-module__customCheckbox___U39ax,
.styles-module__settingsPanel___OxX3Y .styles-module__sliderLabel___U8sPr,
.styles-module__settingsPanel___OxX3Y .styles-module__slider___GLdxp,
.styles-module__settingsPanel___OxX3Y .styles-module__themeToggle___2rUjA {
  transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease;
}
.styles-module__settingsPanel___OxX3Y.styles-module__enter___WFIki {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0px);
  transition: opacity 0.2s ease, transform 0.2s ease, filter 0.2s ease;
}
.styles-module__settingsPanel___OxX3Y.styles-module__exit___fyOJ0 {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
  filter: blur(5px);
  pointer-events: none;
  transition: opacity 0.1s ease, transform 0.1s ease, filter 0.1s ease;
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y {
  background: #1a1a1a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y .styles-module__settingsLabel___8UjfX {
  color: rgba(255, 255, 255, 0.6);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y .styles-module__settingsOption___UNa12 {
  color: rgba(255, 255, 255, 0.85);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y .styles-module__settingsOption___UNa12:hover {
  background: rgba(255, 255, 255, 0.1);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y .styles-module__settingsOption___UNa12.styles-module__selected___OwRqP {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}
[data-agentation-theme=dark] .styles-module__settingsPanel___OxX3Y .styles-module__toggleLabel___Xm8Aa {
  color: rgba(255, 255, 255, 0.85);
}

.styles-module__settingsPanelContainer___Xksv8 {
  overflow: visible;
  position: relative;
  display: flex;
  padding: 0 1rem;
}

.styles-module__settingsPage___6YfHH {
  min-width: 100%;
  flex-shrink: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
  transition-delay: 0s;
  opacity: 1;
}

.styles-module__settingsPage___6YfHH.styles-module__slideLeft___Ps01J {
  transform: translateX(-24px);
  opacity: 0;
  pointer-events: none;
}

.styles-module__automationsPage___uvCq6 {
  position: absolute;
  top: 0;
  left: 24px;
  width: 100%;
  height: 100%;
  padding: 3px 1rem 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0;
  pointer-events: none;
}

.styles-module__automationsPage___uvCq6.styles-module__slideIn___4-qXe {
  transform: translateX(-24px);
  opacity: 1;
  pointer-events: auto;
}

.styles-module__settingsNavLink___wCzJt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: color 0.15s ease;
}
.styles-module__settingsNavLink___wCzJt:hover {
  color: rgba(255, 255, 255, 0.9);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___wCzJt {
  color: rgba(0, 0, 0, 0.5);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___wCzJt:hover {
  color: rgba(0, 0, 0, 0.8);
}
.styles-module__settingsNavLink___wCzJt svg {
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.15s ease;
}
.styles-module__settingsNavLink___wCzJt:hover svg {
  color: #fff;
}
[data-agentation-theme=light] .styles-module__settingsNavLink___wCzJt svg {
  color: rgba(0, 0, 0, 0.25);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___wCzJt:hover svg {
  color: rgba(0, 0, 0, 0.8);
}

.styles-module__settingsNavLinkRight___ZWwhj {
  display: flex;
  align-items: center;
  gap: 6px;
}

.styles-module__mcpNavIndicator___cl9pO {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.styles-module__mcpNavIndicator___cl9pO.styles-module__connected___7c28g {
  background-color: var(--agentation-color-green);
  animation: styles-module__mcpPulse___uNggr 2.5s ease-in-out infinite;
}
.styles-module__mcpNavIndicator___cl9pO.styles-module__connecting___uo-CW {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__mcpPulse___uNggr 1.5s ease-in-out infinite;
}

.styles-module__settingsBackButton___bIe2j {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 0 12px 0;
  margin: -6px 0 0.5rem 0;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 0;
  background: transparent;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: -0.15px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.12s cubic-bezier(0.32, 0.72, 0, 1);
}
.styles-module__settingsBackButton___bIe2j svg {
  opacity: 0.4;
  flex-shrink: 0;
  transition: opacity 0.15s ease, transform 0.18s cubic-bezier(0.32, 0.72, 0, 1);
}
.styles-module__settingsBackButton___bIe2j:hover {
  border-bottom-color: rgba(255, 255, 255, 0.07);
}
.styles-module__settingsBackButton___bIe2j:hover svg {
  opacity: 1;
}
[data-agentation-theme=light] .styles-module__settingsBackButton___bIe2j {
  color: rgba(0, 0, 0, 0.85);
  border-bottom-color: rgba(0, 0, 0, 0.08);
}
[data-agentation-theme=light] .styles-module__settingsBackButton___bIe2j:hover {
  border-bottom-color: rgba(0, 0, 0, 0.08);
}

.styles-module__automationHeader___InP0r {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  font-size: 0.8125rem;
  font-weight: 400;
  color: #fff;
}
[data-agentation-theme=light] .styles-module__automationHeader___InP0r {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__automationDescription___NKlmo {
  font-size: 0.6875rem;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
  line-height: 14px;
}
[data-agentation-theme=light] .styles-module__automationDescription___NKlmo {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__learnMoreLink___8xv-x {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: underline dotted;
  text-decoration-color: rgba(255, 255, 255, 0.2);
  text-underline-offset: 2px;
  transition: color 0.15s ease;
}
.styles-module__learnMoreLink___8xv-x:hover {
  color: #fff;
}
[data-agentation-theme=light] .styles-module__learnMoreLink___8xv-x {
  color: rgba(0, 0, 0, 0.6);
  text-decoration-color: rgba(0, 0, 0, 0.2);
}
[data-agentation-theme=light] .styles-module__learnMoreLink___8xv-x:hover {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__autoSendRow___UblX5 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.styles-module__autoSendLabel___icDc2 {
  font-size: 0.6875rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.15s ease;
}
.styles-module__autoSendLabel___icDc2.styles-module__active___-zoN6 {
  color: #66b8ff;
  color: color(display-p3 0.4 0.72 1);
}
[data-agentation-theme=light] .styles-module__autoSendLabel___icDc2 {
  color: rgba(0, 0, 0, 0.4);
}
[data-agentation-theme=light] .styles-module__autoSendLabel___icDc2.styles-module__active___-zoN6 {
  color: var(--agentation-color-blue);
}

.styles-module__webhookUrlInput___2375C {
  display: block;
  width: 100%;
  flex: 1;
  min-height: 60px;
  box-sizing: border-box;
  margin-top: 11px;
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: 400;
  color: #fff;
  outline: none;
  resize: none;
  user-select: text;
  transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}
.styles-module__webhookUrlInput___2375C::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
.styles-module__webhookUrlInput___2375C:focus {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___2375C {
  border-color: rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.03);
  color: rgba(0, 0, 0, 0.85);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___2375C::placeholder {
  color: rgba(0, 0, 0, 0.3);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___2375C:focus {
  border-color: rgba(0, 0, 0, 0.25);
  background: rgba(0, 0, 0, 0.05);
}

.styles-module__settingsHeader___pwDY9 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
  margin-bottom: 0.5rem;
  padding-bottom: 9px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.styles-module__settingsBrand___0gJeM {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: -0.0094em;
  color: #fff;
  text-decoration: none;
}

.styles-module__settingsBrandSlash___uTG18 {
  color: var(--agentation-color-accent);
  transition: color 0.2s ease;
}

.styles-module__settingsVersion___TUcFq {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
  letter-spacing: -0.0094em;
}

.styles-module__settingsSection___m-YM2 + .styles-module__settingsSection___m-YM2 {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}
.styles-module__settingsSection___m-YM2.styles-module__settingsSectionExtraPadding___jdhFV {
  padding-top: calc(0.5rem + 4px);
}

.styles-module__settingsSectionGrow___h-5HZ {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.styles-module__settingsRow___3sdhc {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
}
.styles-module__settingsRow___3sdhc.styles-module__settingsRowMarginTop___zA0Sp {
  margin-top: 8px;
}

.styles-module__dropdownContainer___BVnxe {
  position: relative;
}

.styles-module__dropdownButton___16NPz {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  letter-spacing: -0.0094em;
}
.styles-module__dropdownButton___16NPz:hover {
  background: rgba(255, 255, 255, 0.08);
}
.styles-module__dropdownButton___16NPz svg {
  opacity: 0.6;
}

.styles-module__cycleButton___FMKfw {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
  border: none;
  background: transparent;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  letter-spacing: -0.0094em;
}
[data-agentation-theme=light] .styles-module__cycleButton___FMKfw {
  color: rgba(0, 0, 0, 0.85);
}
.styles-module__cycleButton___FMKfw:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.styles-module__settingsRowDisabled___EgS0V .styles-module__settingsLabel___8UjfX {
  color: rgba(255, 255, 255, 0.2);
}
[data-agentation-theme=light] .styles-module__settingsRowDisabled___EgS0V .styles-module__settingsLabel___8UjfX {
  color: rgba(0, 0, 0, 0.2);
}
.styles-module__settingsRowDisabled___EgS0V .styles-module__toggleSwitch___l4Ygm {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes styles-module__cycleTextIn___Q6zJf {
  0% {
    opacity: 0;
    transform: translateY(-6px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
.styles-module__cycleButtonText___fD1LR {
  display: inline-block;
  animation: styles-module__cycleTextIn___Q6zJf 0.2s ease-out;
}

.styles-module__cycleDots___LWuoQ {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.styles-module__cycleDot___nPgLY {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0.667);
  transition: background-color 0.25s ease-out, transform 0.25s ease-out;
}
.styles-module__cycleDot___nPgLY.styles-module__active___-zoN6 {
  background: #fff;
  transform: scale(1);
}
[data-agentation-theme=light] .styles-module__cycleDot___nPgLY {
  background: rgba(0, 0, 0, 0.2);
}
[data-agentation-theme=light] .styles-module__cycleDot___nPgLY.styles-module__active___-zoN6 {
  background: rgba(0, 0, 0, 0.7);
}

.styles-module__dropdownMenu___k73ER {
  position: absolute;
  right: 0;
  top: calc(100% + 0.25rem);
  background: #1a1a1a;
  border-radius: 0.5rem;
  padding: 0.25rem;
  min-width: 120px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  z-index: 10;
  animation: styles-module__scaleIn___c-r1K 0.15s ease-out;
}

.styles-module__dropdownItem___ylsLj {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 0.5rem 0.625rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  text-align: left;
  transition: background-color 0.15s ease, color 0.15s ease;
  letter-spacing: -0.0094em;
}
.styles-module__dropdownItem___ylsLj:hover {
  background: rgba(255, 255, 255, 0.08);
}
.styles-module__dropdownItem___ylsLj.styles-module__selected___OwRqP {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-weight: 600;
}

.styles-module__settingsLabel___8UjfX {
  font-size: 0.8125rem;
  font-weight: 400;
  letter-spacing: -0.0094em;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 0.125rem;
}
[data-agentation-theme=light] .styles-module__settingsLabel___8UjfX {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__settingsLabelMarker___ewdtV {
  padding-top: 3px;
  margin-bottom: 10px;
}

.styles-module__settingsOptions___LyrBA {
  display: flex;
  gap: 0.25rem;
}

.styles-module__settingsOption___UNa12 {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  font-size: 0.6875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.styles-module__settingsOption___UNa12:hover {
  background: rgba(0, 0, 0, 0.05);
}
.styles-module__settingsOption___UNa12.styles-module__selected___OwRqP {
  background: color-mix(in srgb, var(--agentation-color-blue) 15%, transparent);
  color: var(--agentation-color-blue);
}

.styles-module__sliderContainer___ducXj {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.styles-module__slider___GLdxp {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.styles-module__slider___GLdxp::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
.styles-module__slider___GLdxp::-moz-range-thumb {
  width: 14px;
  height: 14px;
  background: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
.styles-module__slider___GLdxp:hover::-webkit-slider-thumb {
  transform: scale(1.15);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}
.styles-module__slider___GLdxp:hover::-moz-range-thumb {
  transform: scale(1.15);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

.styles-module__sliderLabels___FhLDB {
  display: flex;
  justify-content: space-between;
}

.styles-module__sliderLabel___U8sPr {
  font-size: 0.625rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: color 0.15s ease;
}
.styles-module__sliderLabel___U8sPr:hover {
  color: rgba(255, 255, 255, 0.7);
}
.styles-module__sliderLabel___U8sPr.styles-module__active___-zoN6 {
  color: rgba(255, 255, 255, 0.9);
}

.styles-module__colorOptions___iHCNX {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.375rem;
  margin-bottom: 1px;
}

.styles-module__colorOption___IodiY {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid transparent;
  background-color: var(--swatch);
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.25, 1, 0.5, 1);
}
@supports (color: color(display-p3 0 0 0)) {
  .styles-module__colorOption___IodiY {
    background-color: var(--swatch-p3);
  }
}
.styles-module__colorOption___IodiY:hover {
  transform: scale(1.15);
}
.styles-module__colorOption___IodiY.styles-module__selected___OwRqP {
  transform: scale(0.83);
}

.styles-module__colorOptionRing___U2xpo {
  display: flex;
  width: 24px;
  height: 24px;
  border: 2px solid transparent;
  border-radius: 50%;
  transition: border-color 0.3s ease;
}
.styles-module__colorOptionRing___U2xpo.styles-module__selected___OwRqP {
  border-color: var(--swatch);
}
@supports (color: color(display-p3 0 0 0)) {
  .styles-module__colorOptionRing___U2xpo.styles-module__selected___OwRqP {
    border-color: var(--swatch-p3);
  }
}

.styles-module__settingsToggle___fBrFn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
.styles-module__settingsToggle___fBrFn + .styles-module__settingsToggle___fBrFn {
  margin-top: calc(0.5rem + 6px);
}
.styles-module__settingsToggle___fBrFn input[type=checkbox] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.styles-module__settingsToggle___fBrFn.styles-module__settingsToggleMarginBottom___MZUyF {
  margin-bottom: calc(0.5rem + 6px);
}

.styles-module__customCheckbox___U39ax {
  position: relative;
  width: 14px;
  height: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.25s ease, border-color 0.25s ease;
}
.styles-module__customCheckbox___U39ax svg {
  color: #1a1a1a;
  opacity: 1;
  transition: opacity 0.15s ease;
}
input[type=checkbox]:checked + .styles-module__customCheckbox___U39ax {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgb(255, 255, 255);
}
[data-agentation-theme=light] .styles-module__customCheckbox___U39ax {
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: #fff;
}
[data-agentation-theme=light] .styles-module__customCheckbox___U39ax.styles-module__checked___mnZLo {
  border-color: #1a1a1a;
  background: #1a1a1a;
}
[data-agentation-theme=light] .styles-module__customCheckbox___U39ax.styles-module__checked___mnZLo svg {
  color: #fff;
}

.styles-module__toggleLabel___Xm8Aa {
  font-size: 0.8125rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: -0.0094em;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
[data-agentation-theme=light] .styles-module__toggleLabel___Xm8Aa {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__toggleSwitch___l4Ygm {
  position: relative;
  display: inline-block;
  width: 24px;
  height: 16px;
  flex-shrink: 0;
  cursor: pointer;
  transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.styles-module__toggleSwitch___l4Ygm input {
  opacity: 0;
  width: 0;
  height: 0;
}
.styles-module__toggleSwitch___l4Ygm input:checked + .styles-module__toggleSlider___wprIn {
  background-color: var(--agentation-color-blue);
}
.styles-module__toggleSwitch___l4Ygm input:checked + .styles-module__toggleSlider___wprIn::before {
  transform: translateX(8px);
}
.styles-module__toggleSwitch___l4Ygm.styles-module__disabled___332Jw {
  opacity: 0.4;
}
.styles-module__toggleSwitch___l4Ygm.styles-module__disabled___332Jw .styles-module__toggleSlider___wprIn {
  cursor: not-allowed;
}

.styles-module__toggleSlider___wprIn {
  position: absolute;
  cursor: pointer;
  inset: 0;
  border-radius: 16px;
  background: #484848;
}
[data-agentation-theme=light] .styles-module__toggleSlider___wprIn {
  background: #dddddd;
}
.styles-module__toggleSlider___wprIn::before {
  content: "";
  position: absolute;
  height: 12px;
  width: 12px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes styles-module__mcpPulse___uNggr {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-green) 50%, transparent);
  }
  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--agentation-color-green) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-green) 0%, transparent);
  }
}
@keyframes styles-module__mcpPulseError___fov9B {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-red) 50%, transparent);
  }
  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--agentation-color-red) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-red) 0%, transparent);
  }
}
.styles-module__mcpStatusDot___ibgkc {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.styles-module__mcpStatusDot___ibgkc.styles-module__connecting___uo-CW {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__mcpPulse___uNggr 1.5s infinite;
}
.styles-module__mcpStatusDot___ibgkc.styles-module__connected___7c28g {
  background-color: var(--agentation-color-green);
  animation: styles-module__mcpPulse___uNggr 2.5s ease-in-out infinite;
}
.styles-module__mcpStatusDot___ibgkc.styles-module__disconnected___cHPxR {
  background-color: var(--agentation-color-red);
  animation: styles-module__mcpPulseError___fov9B 2s infinite;
}

.styles-module__drawCanvas___7cG9U {
  position: fixed;
  inset: 0;
  z-index: 99996;
  pointer-events: none !important;
}
.styles-module__drawCanvas___7cG9U.styles-module__active___-zoN6 {
  pointer-events: auto !important;
  cursor: crosshair !important;
}
.styles-module__drawCanvas___7cG9U.styles-module__active___-zoN6[data-stroke-hover] {
  cursor: pointer !important;
}

.styles-module__dragSelection___kZLq2 {
  position: fixed;
  top: 0;
  left: 0;
  border: 2px solid color-mix(in srgb, var(--agentation-color-green) 60%, transparent);
  border-radius: 4px;
  background-color: color-mix(in srgb, var(--agentation-color-green) 8%, transparent);
  pointer-events: none;
  z-index: 99997;
  will-change: transform, width, height;
  contain: layout style;
}

.styles-module__dragCount___KM90j {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: var(--agentation-color-green);
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  min-width: 1.5rem;
  text-align: center;
}

.styles-module__highlightsContainer___-0xzG {
  position: fixed;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 99996;
}

.styles-module__selectedElementHighlight___fyVlI {
  position: fixed;
  top: 0;
  left: 0;
  border: 2px solid color-mix(in srgb, var(--agentation-color-green) 50%, transparent);
  border-radius: 4px;
  background: color-mix(in srgb, var(--agentation-color-green) 6%, transparent);
  pointer-events: none;
  will-change: transform, width, height;
  contain: layout style;
}

[data-agentation-theme=light] .styles-module__toolbarContainer___dIhma {
  background: #fff;
  color: rgba(0, 0, 0, 0.85);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04);
}
[data-agentation-theme=light] .styles-module__toolbarContainer___dIhma.styles-module__collapsed___Rydsn:hover {
  background: #f5f5f5;
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc {
  color: rgba(0, 0, 0, 0.5);
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc:hover:not(:disabled):not([data-active=true]):not([data-failed=true]):not([data-auto-sync=true]):not([data-error=true]):not([data-no-hover=true]) {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.85);
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc[data-active=true] {
  color: var(--agentation-color-blue);
  background: color-mix(in srgb, var(--agentation-color-blue) 15%, transparent);
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc[data-error=true] {
  color: var(--agentation-color-red);
  background: color-mix(in srgb, var(--agentation-color-red) 15%, transparent);
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc[data-danger]:hover:not(:disabled):not([data-active=true]):not([data-failed=true]) {
  color: var(--agentation-color-red);
  background: color-mix(in srgb, var(--agentation-color-red) 15%, transparent);
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc[data-auto-sync=true] {
  color: var(--agentation-color-green);
  background: transparent;
}
[data-agentation-theme=light] .styles-module__controlButton___8Q0jc[data-failed=true] {
  color: var(--agentation-color-red);
  background: color-mix(in srgb, var(--agentation-color-red) 15%, transparent);
}
[data-agentation-theme=light] .styles-module__buttonTooltip___Burd9 {
  background: #fff;
  color: rgba(0, 0, 0, 0.85);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04);
}
[data-agentation-theme=light] .styles-module__buttonTooltip___Burd9::after {
  background: #fff;
}
[data-agentation-theme=light] .styles-module__divider___c--s1 {
  background: rgba(0, 0, 0, 0.1);
}`,dx={toolbar:"styles-module__toolbar___wNsdK",markersLayer:"styles-module__markersLayer___-25j1",fixedMarkersLayer:"styles-module__fixedMarkersLayer___ffyX6",controlsContent:"styles-module__controlsContent___9GJWU",disableTransitions:"styles-module__disableTransitions___EopxO",toolbarContainer:"styles-module__toolbarContainer___dIhma",entrance:"styles-module__entrance___sgHd8",toolbarEnter:"styles-module__toolbarEnter___u8RRu",hiding:"styles-module__hiding___1td44",toolbarHide:"styles-module__toolbarHide___y8kaT",collapsed:"styles-module__collapsed___Rydsn",expanded:"styles-module__expanded___ofKPx",serverConnected:"styles-module__serverConnected___Gfbou",toggleContent:"styles-module__toggleContent___0yfyP",visible:"styles-module__visible___KHwEW",hidden:"styles-module__hidden___Ae8H4",badge:"styles-module__badge___2XsgF",fadeOut:"styles-module__fadeOut___6Ut6-",badgeEnter:"styles-module__badgeEnter___mVQLj",controlButton:"styles-module__controlButton___8Q0jc",statusShowing:"styles-module__statusShowing___te6iu",buttonBadge:"styles-module__buttonBadge___NeFWb",mcpIndicator:"styles-module__mcpIndicator___zGJeL",connected:"styles-module__connected___7c28g",mcpIndicatorPulseConnected:"styles-module__mcpIndicatorPulseConnected___EDodZ",connecting:"styles-module__connecting___uo-CW",mcpIndicatorPulseConnecting:"styles-module__mcpIndicatorPulseConnecting___cCYte",connectionIndicatorWrapper:"styles-module__connectionIndicatorWrapper___L-e-3",connectionIndicator:"styles-module__connectionIndicator___afk9p",connectionIndicatorVisible:"styles-module__connectionIndicatorVisible___C-i5B",connectionIndicatorConnected:"styles-module__connectionIndicatorConnected___IY8pR",connectionPulse:"styles-module__connectionPulse___-Zycw",connectionIndicatorDisconnected:"styles-module__connectionIndicatorDisconnected___kmpaZ",connectionIndicatorConnecting:"styles-module__connectionIndicatorConnecting___QmSLH",buttonWrapper:"styles-module__buttonWrapper___rBcdv",buttonTooltip:"styles-module__buttonTooltip___Burd9",tooltipsInSession:"styles-module__tooltipsInSession___-0lHH",sendButtonWrapper:"styles-module__sendButtonWrapper___UUxG6",sendButtonVisible:"styles-module__sendButtonVisible___WPSQU",shortcut:"styles-module__shortcut___lEAQk",tooltipBelow:"styles-module__tooltipBelow___m6ats",tooltipsHidden:"styles-module__tooltipsHidden___VtLJG",tooltipVisible:"styles-module__tooltipVisible___0jcCv",buttonWrapperAlignLeft:"styles-module__buttonWrapperAlignLeft___myzIp",buttonWrapperAlignRight:"styles-module__buttonWrapperAlignRight___HCQFR",divider:"styles-module__divider___c--s1",overlay:"styles-module__overlay___Q1O9y",hoverHighlight:"styles-module__hoverHighlight___ogakW",enter:"styles-module__enter___WFIki",hoverHighlightIn:"styles-module__hoverHighlightIn___6WYHY",multiSelectOutline:"styles-module__multiSelectOutline___cSJ-m",fadeIn:"styles-module__fadeIn___b9qmf",exit:"styles-module__exit___fyOJ0",singleSelectOutline:"styles-module__singleSelectOutline___QhX-O",hoverTooltip:"styles-module__hoverTooltip___bvLk7",hoverTooltipIn:"styles-module__hoverTooltipIn___FYGQx",hoverReactPath:"styles-module__hoverReactPath___gx1IJ",hoverElementName:"styles-module__hoverElementName___QMLMl",marker:"styles-module__marker___6sQrs",clearing:"styles-module__clearing___FQ--7",markerIn:"styles-module__markerIn___5FaAP",markerOut:"styles-module__markerOut___GU5jX",pending:"styles-module__pending___2IHLC",fixed:"styles-module__fixed___dBMHC",multiSelect:"styles-module__multiSelect___YWiuz",hovered:"styles-module__hovered___ZgXIy",renumber:"styles-module__renumber___nCTxD",renumberRoll:"styles-module__renumberRoll___Wgbq3",markerTooltip:"styles-module__markerTooltip___aLJID",tooltipIn:"styles-module__tooltipIn___0N31w",markerQuote:"styles-module__markerQuote___FHmrz",markerNote:"styles-module__markerNote___QkrrS",markerHint:"styles-module__markerHint___2iF-6",settingsPanel:"styles-module__settingsPanel___OxX3Y",settingsHeader:"styles-module__settingsHeader___pwDY9",settingsBrand:"styles-module__settingsBrand___0gJeM",settingsBrandSlash:"styles-module__settingsBrandSlash___uTG18",settingsVersion:"styles-module__settingsVersion___TUcFq",settingsSection:"styles-module__settingsSection___m-YM2",settingsLabel:"styles-module__settingsLabel___8UjfX",cycleButton:"styles-module__cycleButton___FMKfw",cycleDot:"styles-module__cycleDot___nPgLY",dropdownButton:"styles-module__dropdownButton___16NPz",toggleLabel:"styles-module__toggleLabel___Xm8Aa",customCheckbox:"styles-module__customCheckbox___U39ax",sliderLabel:"styles-module__sliderLabel___U8sPr",slider:"styles-module__slider___GLdxp",themeToggle:"styles-module__themeToggle___2rUjA",settingsOption:"styles-module__settingsOption___UNa12",selected:"styles-module__selected___OwRqP",settingsPanelContainer:"styles-module__settingsPanelContainer___Xksv8",settingsPage:"styles-module__settingsPage___6YfHH",slideLeft:"styles-module__slideLeft___Ps01J",automationsPage:"styles-module__automationsPage___uvCq6",slideIn:"styles-module__slideIn___4-qXe",settingsNavLink:"styles-module__settingsNavLink___wCzJt",settingsNavLinkRight:"styles-module__settingsNavLinkRight___ZWwhj",mcpNavIndicator:"styles-module__mcpNavIndicator___cl9pO",mcpPulse:"styles-module__mcpPulse___uNggr",settingsBackButton:"styles-module__settingsBackButton___bIe2j",automationHeader:"styles-module__automationHeader___InP0r",automationDescription:"styles-module__automationDescription___NKlmo",learnMoreLink:"styles-module__learnMoreLink___8xv-x",autoSendRow:"styles-module__autoSendRow___UblX5",autoSendLabel:"styles-module__autoSendLabel___icDc2",active:"styles-module__active___-zoN6",webhookUrlInput:"styles-module__webhookUrlInput___2375C",settingsSectionExtraPadding:"styles-module__settingsSectionExtraPadding___jdhFV",settingsSectionGrow:"styles-module__settingsSectionGrow___h-5HZ",settingsRow:"styles-module__settingsRow___3sdhc",settingsRowMarginTop:"styles-module__settingsRowMarginTop___zA0Sp",dropdownContainer:"styles-module__dropdownContainer___BVnxe",settingsRowDisabled:"styles-module__settingsRowDisabled___EgS0V",toggleSwitch:"styles-module__toggleSwitch___l4Ygm",cycleButtonText:"styles-module__cycleButtonText___fD1LR",cycleTextIn:"styles-module__cycleTextIn___Q6zJf",cycleDots:"styles-module__cycleDots___LWuoQ",dropdownMenu:"styles-module__dropdownMenu___k73ER",scaleIn:"styles-module__scaleIn___c-r1K",dropdownItem:"styles-module__dropdownItem___ylsLj",settingsLabelMarker:"styles-module__settingsLabelMarker___ewdtV",settingsOptions:"styles-module__settingsOptions___LyrBA",sliderContainer:"styles-module__sliderContainer___ducXj",sliderLabels:"styles-module__sliderLabels___FhLDB",colorOptions:"styles-module__colorOptions___iHCNX",colorOption:"styles-module__colorOption___IodiY",colorOptionRing:"styles-module__colorOptionRing___U2xpo",settingsToggle:"styles-module__settingsToggle___fBrFn",settingsToggleMarginBottom:"styles-module__settingsToggleMarginBottom___MZUyF",checked:"styles-module__checked___mnZLo",toggleSlider:"styles-module__toggleSlider___wprIn",disabled:"styles-module__disabled___332Jw",mcpStatusDot:"styles-module__mcpStatusDot___ibgkc",disconnected:"styles-module__disconnected___cHPxR",mcpPulseError:"styles-module__mcpPulseError___fov9B",drawCanvas:"styles-module__drawCanvas___7cG9U",dragSelection:"styles-module__dragSelection___kZLq2",dragCount:"styles-module__dragCount___KM90j",highlightsContainer:"styles-module__highlightsContainer___-0xzG",selectedElementHighlight:"styles-module__selectedElementHighlight___fyVlI",scaleOut:"styles-module__scaleOut___Wctwz",slideUp:"styles-module__slideUp___kgD36",slideDown:"styles-module__slideDown___zcdje"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-page-toolbar-css-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-page-toolbar-css-styles",document.head.appendChild(e)),e.textContent=cx}var W=dx,Pi=[{value:"compact",label:"Compact"},{value:"standard",label:"Standard"},{value:"detailed",label:"Detailed"},{value:"forensic",label:"Forensic"}];function mp(e,t,n="standard"){if(e.length===0)return"";let o=typeof window<"u"?`${window.innerWidth}\xD7${window.innerHeight}`:"unknown",r=`## Page Feedback: ${t}
`;return n==="forensic"?(r+=`
**Environment:**
`,r+=`- Viewport: ${o}
`,typeof window<"u"&&(r+=`- URL: ${window.location.href}
`,r+=`- User Agent: ${navigator.userAgent}
`,r+=`- Timestamp: ${new Date().toISOString()}
`,r+=`- Device Pixel Ratio: ${window.devicePixelRatio}
`),r+=`
---
`):n!=="compact"&&(r+=`**Viewport:** ${o}
`),r+=`
`,e.forEach((l,i)=>{n==="compact"?(r+=`${i+1}. **${l.element}**${l.sourceFile?` (${l.sourceFile})`:""}: ${l.comment}`,l.selectedText&&(r+=` (re: "${l.selectedText.slice(0,30)}${l.selectedText.length>30?"...":""}")`),r+=`
`):n==="forensic"?(r+=`### ${i+1}. ${l.element}
`,l.isMultiSelect&&l.fullPath&&(r+=`*Forensic data shown for first element of selection*
`),l.fullPath&&(r+=`**Full DOM Path:** ${l.fullPath}
`),l.cssClasses&&(r+=`**CSS Classes:** ${l.cssClasses}
`),l.boundingBox&&(r+=`**Position:** x:${Math.round(l.boundingBox.x)}, y:${Math.round(l.boundingBox.y)} (${Math.round(l.boundingBox.width)}\xD7${Math.round(l.boundingBox.height)}px)
`),r+=`**Annotation at:** ${l.x.toFixed(1)}% from left, ${Math.round(l.y)}px from top
`,l.selectedText&&(r+=`**Selected text:** "${l.selectedText}"
`),l.nearbyText&&!l.selectedText&&(r+=`**Context:** ${l.nearbyText.slice(0,100)}
`),l.computedStyles&&(r+=`**Computed Styles:** ${l.computedStyles}
`),l.accessibility&&(r+=`**Accessibility:** ${l.accessibility}
`),l.nearbyElements&&(r+=`**Nearby Elements:** ${l.nearbyElements}
`),l.sourceFile&&(r+=`**Source:** ${l.sourceFile}
`),l.reactComponents&&(r+=`**React:** ${l.reactComponents}
`),r+=`**Feedback:** ${l.comment}

`):(r+=`### ${i+1}. ${l.element}
`,r+=`**Location:** ${l.elementPath}
`,l.sourceFile&&(r+=`**Source:** ${l.sourceFile}
`),l.reactComponents&&(r+=`**React:** ${l.reactComponents}
`),n==="detailed"&&(l.cssClasses&&(r+=`**Classes:** ${l.cssClasses}
`),l.boundingBox&&(r+=`**Position:** ${Math.round(l.boundingBox.x)}px, ${Math.round(l.boundingBox.y)}px (${Math.round(l.boundingBox.width)}\xD7${Math.round(l.boundingBox.height)}px)
`)),l.selectedText&&(r+=`**Selected text:** "${l.selectedText}"
`),n==="detailed"&&l.nearbyText&&!l.selectedText&&(r+=`**Context:** ${l.nearbyText.slice(0,100)}
`),r+=`**Feedback:** ${l.comment}

`)}),r.trim()}var ux=`@keyframes styles-module__markerIn___x4G8D {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.3);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}
@keyframes styles-module__markerOut___6VhQN {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.3);
  }
}
@keyframes styles-module__tooltipIn___aJslQ {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(2px) scale(0.891);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(0.909);
  }
}
@keyframes styles-module__renumberRoll___akV9B {
  0% {
    transform: translateX(-40%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}
.styles-module__marker___9CKF7 {
  position: absolute;
  width: 22px;
  height: 22px;
  background: var(--agentation-color-blue);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 600;
  transform: translate(-50%, -50%) scale(1);
  opacity: 1;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2), inset 0 0 0 1px rgba(0, 0, 0, 0.04);
  user-select: none;
  will-change: transform, opacity;
  contain: layout style;
  z-index: 1;
}
.styles-module__marker___9CKF7:hover {
  z-index: 2;
}
.styles-module__marker___9CKF7:not(.styles-module__enter___8kI3q):not(.styles-module__exit___KBdR3):not(.styles-module__clearing___8rM7K) {
  transition: background-color 0.15s ease, transform 0.1s ease;
}
.styles-module__marker___9CKF7.styles-module__enter___8kI3q {
  animation: styles-module__markerIn___x4G8D 0.25s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.styles-module__marker___9CKF7.styles-module__exit___KBdR3 {
  animation: styles-module__markerOut___6VhQN 0.2s ease-out both;
  pointer-events: none;
}
.styles-module__marker___9CKF7.styles-module__clearing___8rM7K {
  animation: styles-module__markerOut___6VhQN 0.15s ease-out both;
  pointer-events: none;
}
.styles-module__marker___9CKF7:not(.styles-module__enter___8kI3q):not(.styles-module__exit___KBdR3):not(.styles-module__clearing___8rM7K):hover {
  transform: translate(-50%, -50%) scale(1.1);
}
.styles-module__marker___9CKF7.styles-module__pending___BiY-U {
  position: fixed;
  background-color: var(--agentation-color-blue);
  cursor: default;
}
.styles-module__marker___9CKF7.styles-module__fixed___aKrQO {
  position: fixed;
}
.styles-module__marker___9CKF7.styles-module__multiSelect___CPfTC {
  background-color: var(--agentation-color-green);
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-size: 0.75rem;
}
.styles-module__marker___9CKF7.styles-module__multiSelect___CPfTC.styles-module__pending___BiY-U {
  background-color: var(--agentation-color-green);
}
.styles-module__marker___9CKF7.styles-module__hovered___-mg2N {
  background-color: var(--agentation-color-red);
}

.styles-module__renumber___16lvD {
  display: block;
  animation: styles-module__renumberRoll___akV9B 0.2s ease-out;
}

.styles-module__markerTooltip___-VUm- {
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%) scale(0.909);
  z-index: 100002;
  background: #1a1a1a;
  padding: 8px 0.75rem;
  border-radius: 0.75rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-weight: 400;
  color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08);
  min-width: 120px;
  max-width: 200px;
  pointer-events: none;
  cursor: default;
}
.styles-module__markerTooltip___-VUm-.styles-module__enter___8kI3q {
  animation: styles-module__tooltipIn___aJslQ 0.1s ease-out forwards;
}

.styles-module__markerQuote___tQake {
  display: block;
  font-size: 12px;
  font-style: italic;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.3125rem;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.styles-module__markerNote___Rh4eI {
  display: block;
  font-size: 13px;
  font-weight: 400;
  line-height: 1.4;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-bottom: 2px;
}

[data-agentation-theme=light] .styles-module__markerTooltip___-VUm- {
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.06);
}
[data-agentation-theme=light] .styles-module__markerTooltip___-VUm- .styles-module__markerQuote___tQake {
  color: rgba(0, 0, 0, 0.5);
}
[data-agentation-theme=light] .styles-module__markerTooltip___-VUm- .styles-module__markerNote___Rh4eI {
  color: rgba(0, 0, 0, 0.85);
}`,_x={marker:"styles-module__marker___9CKF7",enter:"styles-module__enter___8kI3q",exit:"styles-module__exit___KBdR3",clearing:"styles-module__clearing___8rM7K",markerIn:"styles-module__markerIn___x4G8D",markerOut:"styles-module__markerOut___6VhQN",pending:"styles-module__pending___BiY-U",fixed:"styles-module__fixed___aKrQO",multiSelect:"styles-module__multiSelect___CPfTC",hovered:"styles-module__hovered___-mg2N",renumber:"styles-module__renumber___16lvD",renumberRoll:"styles-module__renumberRoll___akV9B",markerTooltip:"styles-module__markerTooltip___-VUm-",tooltipIn:"styles-module__tooltipIn___aJslQ",markerQuote:"styles-module__markerQuote___tQake",markerNote:"styles-module__markerNote___Rh4eI"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-annotation-marker-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-annotation-marker-styles",document.head.appendChild(e)),e.textContent=ux}var Pt=_x;function gp({annotation:e,globalIndex:t,layerIndex:n,layerSize:o,isExiting:r,isClearing:l,isAnimated:i,isHovered:s,isDeleting:a,isEditingAny:m,renumberFrom:p,markerClickBehavior:b,tooltipStyle:y,onHoverEnter:R,onHoverLeave:C,onClick:N,onContextMenu:L}){let f=(s||a)&&!m,g=f&&b==="delete",w=e.isMultiSelect,$=w?"var(--agentation-color-green)":"var(--agentation-color-accent)",U=r?Pt.exit:l?Pt.clearing:i?"":Pt.enter,V=r?`${(o-1-n)*20}ms`:`${n*20}ms`;return(0,Cn.jsxs)("div",{className:`${Pt.marker} ${w?Pt.multiSelect:""} ${U} ${g?Pt.hovered:""}`,"data-annotation-marker":!0,style:{left:`${e.x}%`,top:e.y,backgroundColor:g?void 0:$,animationDelay:V},onMouseEnter:()=>R(e),onMouseLeave:C,onClick:B=>{B.stopPropagation(),r||N(e)},onContextMenu:L?B=>{b==="delete"&&(B.preventDefault(),B.stopPropagation(),r||L(e))}:void 0,children:[f?g?(0,Cn.jsx)(Bu,{size:w?18:16}):(0,Cn.jsx)(Dp,{size:16}):(0,Cn.jsx)("span",{className:p!==null&&t>=p?Pt.renumber:void 0,children:t+1}),s&&!m&&(0,Cn.jsxs)("div",{className:`${Pt.markerTooltip} ${Pt.enter}`,style:y,children:[(0,Cn.jsxs)("span",{className:Pt.markerQuote,children:[e.element,e.selectedText&&` "${e.selectedText.slice(0,30)}${e.selectedText.length>30?"...":""}"`]}),(0,Cn.jsx)("span",{className:Pt.markerNote,children:e.comment})]})]})}function fx({x:e,y:t,isMultiSelect:n,isExiting:o}){return(0,Cn.jsx)("div",{className:`${Pt.marker} ${Pt.pending} ${n?Pt.multiSelect:""} ${o?Pt.exit:Pt.enter}`,style:{left:`${e}%`,top:t,backgroundColor:n?"var(--agentation-color-green)":"var(--agentation-color-accent)"},children:(0,Cn.jsx)(kp,{size:12})})}function yp({annotation:e,fixed:t}){let n=e.isMultiSelect;return(0,Cn.jsx)("div",{className:`${Pt.marker} ${t?Pt.fixed:""} ${Pt.hovered} ${n?Pt.multiSelect:""} ${Pt.exit}`,"data-annotation-marker":!0,style:{left:`${e.x}%`,top:e.y},children:(0,Cn.jsx)(Bu,{size:n?12:10})})}var hx=`.styles-module__switchContainer___Ka-AB {
  display: flex;
  align-items: center;
  position: relative;
  padding: 2px;
  width: 24px;
  height: 16px;
  border-radius: 8px;
  background-color: #cdcdcd;
  transition: background-color 0.15s, opacity 0.15s;
}
[data-agentation-theme=dark] .styles-module__switchContainer___Ka-AB {
  background-color: #484848;
}
.styles-module__switchContainer___Ka-AB:has(.styles-module__switchInput___kYDSD:checked) {
  background-color: var(--agentation-color-blue);
}
.styles-module__switchContainer___Ka-AB:has(.styles-module__switchInput___kYDSD:disabled) {
  opacity: 0.3;
}

.styles-module__switchInput___kYDSD {
  position: absolute;
  z-index: 1;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  cursor: pointer;
}
.styles-module__switchInput___kYDSD:disabled {
  cursor: not-allowed;
}

.styles-module__switchThumb___4sCPH {
  border-radius: 50%;
  width: 12px;
  height: 12px;
  background-color: #fff;
  transition: transform 0.15s;
}
.styles-module__switchContainer___Ka-AB:has(.styles-module__switchInput___kYDSD:checked) .styles-module__switchThumb___4sCPH {
  transform: translateX(8px);
}`,px={switchContainer:"styles-module__switchContainer___Ka-AB",switchInput:"styles-module__switchInput___kYDSD",switchThumb:"styles-module__switchThumb___4sCPH"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-switch-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-switch-styles",document.head.appendChild(e)),e.textContent=hx}var ku=px,Cu=({className:e="",...t})=>(0,Oi.jsxs)("div",{className:`${ku.switchContainer} ${e}`,children:[(0,Oi.jsx)("input",{className:ku.switchInput,type:"checkbox",...t}),(0,Oi.jsx)("div",{className:ku.switchThumb})]}),mx=`.styles-module__checkboxContainer___joqZk {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  border: 1px solid rgba(26, 26, 26, 0.2);
  border-radius: 4px;
  width: 14px;
  height: 14px;
  background-color: #fff;
  transition: background-color 0.2s ease;
}
[data-agentation-theme=dark] .styles-module__checkboxContainer___joqZk {
  border-color: rgba(255, 255, 255, 0.2);
  background-color: #252525;
}
.styles-module__checkboxContainer___joqZk:has(.styles-module__checkboxInput___ECzzO:checked) {
  background-color: #1a1a1a;
}
[data-agentation-theme=dark] .styles-module__checkboxContainer___joqZk:has(.styles-module__checkboxInput___ECzzO:checked) {
  background-color: #fff;
}

.styles-module__checkboxInput___ECzzO {
  position: absolute;
  z-index: 1;
  inset: -1px;
  border-radius: inherit;
  opacity: 0;
  cursor: pointer;
}

.styles-module__checkboxCheck___fUXpr {
  color: #fafafa;
}
[data-agentation-theme=dark] .styles-module__checkboxCheck___fUXpr {
  color: #1a1a1a;
}

.styles-module__checkboxCheckPath___cDyh8 {
  stroke-dasharray: 9.29px;
  stroke-dashoffset: 9.29px;
  color: #fafafa;
  transition: stroke-dashoffset 0.1s ease;
}
[data-agentation-theme=dark] .styles-module__checkboxCheckPath___cDyh8 {
  color: #1a1a1a;
}
.styles-module__checkboxContainer___joqZk:has(.styles-module__checkboxInput___ECzzO:checked) .styles-module__checkboxCheckPath___cDyh8 {
  transition-duration: 0.2s;
  stroke-dashoffset: 0;
}`,gx={checkboxContainer:"styles-module__checkboxContainer___joqZk",checkboxInput:"styles-module__checkboxInput___ECzzO",checkboxCheck:"styles-module__checkboxCheck___fUXpr",checkboxCheckPath:"styles-module__checkboxCheckPath___cDyh8"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-checkbox-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-checkbox-styles",document.head.appendChild(e)),e.textContent=mx}var $a=gx,yx=({className:e="",...t})=>(0,Cl.jsxs)("div",{className:`${$a.checkboxContainer} ${e}`,children:[(0,Cl.jsx)("input",{className:$a.checkboxInput,type:"checkbox",...t}),(0,Cl.jsx)("svg",{className:$a.checkboxCheck,width:"14",height:"14",viewBox:"0 0 14 14",fill:"none",children:(0,Cl.jsx)("path",{className:$a.checkboxCheckPath,d:"M3.94 7L6.13 9.19L10.5 4.81",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})})]}),xx=`.styles-module__container___w8eAF {
  display: flex;
  align-items: center;
  height: 24px;
}

.styles-module__label___J5mxE {
  padding-inline: 8px 2px;
  line-height: 20px;
  font-size: 13px;
  letter-spacing: -0.15px;
  color: rgba(26, 26, 26, 0.5);
  cursor: pointer;
}
[data-agentation-theme=dark] .styles-module__label___J5mxE {
  color: rgba(255, 255, 255, 0.5);
}`,vx={container:"styles-module__container___w8eAF",label:"styles-module__label___J5mxE"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-checkbox-field-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-checkbox-field-styles",document.head.appendChild(e)),e.textContent=xx}var xp=vx,vp=({className:e="",label:t,tooltip:n,checked:o,onChange:r,...l})=>{let i=(0,tm.useId)();return(0,Sl.jsxs)("div",{className:`${xp.container} ${e}`,...l,children:[(0,Sl.jsx)(yx,{id:i,onChange:r,checked:o}),(0,Sl.jsx)("label",{className:xp.label,htmlFor:i,children:t}),n&&(0,Sl.jsx)(Nr,{content:n})]})},wx=`@keyframes styles-module__cycleTextIn___VBNTi {
  0% {
    opacity: 0;
    transform: translateY(-6px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes styles-module__scaleIn___QpQ8E {
  from {
    opacity: 0;
    transform: scale(0.85);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes styles-module__mcpPulse___5Q3Jj {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-green) 50%, transparent);
  }
  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--agentation-color-green) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-green) 0%, transparent);
  }
}
@keyframes styles-module__mcpPulseError___VHxhx {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-red) 50%, transparent);
  }
  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--agentation-color-red) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--agentation-color-red) 0%, transparent);
  }
}
@keyframes styles-module__themeIconIn___qUWMV {
  0% {
    opacity: 0;
    transform: scale(0.8) rotate(-30deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}
.styles-module__settingsPanel___qNkn- {
  position: absolute;
  right: 5px;
  bottom: calc(100% + 0.5rem);
  z-index: 1;
  overflow: hidden;
  background: #1c1c1c;
  border-radius: 16px;
  padding: 12px 0;
  width: 100%;
  max-width: 253px;
  min-width: 205px;
  cursor: default;
  opacity: 1;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.04);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.styles-module__settingsPanel___qNkn-::before, .styles-module__settingsPanel___qNkn-::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 16px;
  z-index: 2;
  pointer-events: none;
}
.styles-module__settingsPanel___qNkn-::before {
  left: 0;
  background: linear-gradient(to right, #1c1c1c 0%, transparent 100%);
}
.styles-module__settingsPanel___qNkn-::after {
  right: 0;
  background: linear-gradient(to left, #1c1c1c 0%, transparent 100%);
}
.styles-module__settingsPanel___qNkn- .styles-module__settingsHeader___Fn1DP,
.styles-module__settingsPanel___qNkn- .styles-module__settingsBrand___OoKlM,
.styles-module__settingsPanel___qNkn- .styles-module__settingsBrandSlash___Q-AU9,
.styles-module__settingsPanel___qNkn- .styles-module__settingsVersion___rXmL9,
.styles-module__settingsPanel___qNkn- .styles-module__settingsSection___n5V-4,
.styles-module__settingsPanel___qNkn- .styles-module__settingsLabel___VCVOQ,
.styles-module__settingsPanel___qNkn- .styles-module__cycleButton___XMBx3,
.styles-module__settingsPanel___qNkn- .styles-module__cycleDot___zgSXY,
.styles-module__settingsPanel___qNkn- .styles-module__dropdownButton___mKHe8,
.styles-module__settingsPanel___qNkn- .styles-module__sliderLabel___6K5v1,
.styles-module__settingsPanel___qNkn- .styles-module__slider___v5z-c,
.styles-module__settingsPanel___qNkn- .styles-module__themeToggle___3imlT {
  transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease;
}
.styles-module__settingsPanel___qNkn-.styles-module__enter___wginS {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0px);
  transition: opacity 0.2s ease, transform 0.2s ease, filter 0.2s ease;
}
.styles-module__settingsPanel___qNkn-.styles-module__exit___A4iJc {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
  filter: blur(5px);
  pointer-events: none;
  transition: opacity 0.1s ease, transform 0.1s ease, filter 0.1s ease;
}
[data-agentation-theme=dark] .styles-module__settingsPanel___qNkn- {
  background: #1a1a1a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___qNkn- .styles-module__settingsLabel___VCVOQ {
  color: rgba(255, 255, 255, 0.6);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___qNkn- .styles-module__settingsOption___JoyH- {
  color: rgba(255, 255, 255, 0.85);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___qNkn- .styles-module__settingsOption___JoyH-:hover {
  background: rgba(255, 255, 255, 0.1);
}
[data-agentation-theme=dark] .styles-module__settingsPanel___qNkn- .styles-module__settingsOption___JoyH-.styles-module__selected___k1-Vq {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.styles-module__settingsPanelContainer___5it-H {
  overflow: visible;
  position: relative;
  display: flex;
  padding: 0 16px;
}

.styles-module__settingsPage___BMn-3 {
  min-width: 100%;
  flex-basis: 0;
  flex-shrink: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
  transition-delay: 0s;
  opacity: 1;
}

.styles-module__settingsPage___BMn-3.styles-module__slideLeft___qUvW4 {
  transform: translateX(-24px);
  opacity: 0;
  pointer-events: none;
}

.styles-module__automationsPage___N7By0 {
  position: absolute;
  top: 0;
  left: 24px;
  width: 100%;
  height: 100%;
  padding: 0 16px 4px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0;
  pointer-events: none;
}

.styles-module__automationsPage___N7By0.styles-module__slideIn___uXDSu {
  transform: translateX(-24px);
  opacity: 1;
  pointer-events: auto;
}

.styles-module__settingsHeader___Fn1DP {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px;
}

.styles-module__settingsBrand___OoKlM {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: -0.0094em;
  color: #fff;
  text-decoration: none;
}

.styles-module__settingsBrandSlash___Q-AU9 {
  color: var(--agentation-color-accent);
  transition: color 0.2s ease;
}

.styles-module__settingsVersion___rXmL9 {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
  letter-spacing: -0.0094em;
}

.styles-module__themeToggle___3imlT {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  transition: background-color 0.15s ease, color 0.15s ease;
  cursor: pointer;
}
.styles-module__themeToggle___3imlT:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}
[data-agentation-theme=light] .styles-module__themeToggle___3imlT {
  color: rgba(0, 0, 0, 0.4);
}
[data-agentation-theme=light] .styles-module__themeToggle___3imlT:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.7);
}

.styles-module__themeIconWrapper___pyaYa {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 20px;
  height: 20px;
}

.styles-module__themeIcon___w7lAm {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: styles-module__themeIconIn___qUWMV 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.styles-module__settingsSectionGrow___eZTRw {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.styles-module__settingsRow___y-tDE {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
}
.styles-module__settingsRow___y-tDE.styles-module__settingsRowMarginTop___uLpGb {
  margin-top: 8px;
}

.styles-module__settingsRowDisabled___ydl3Q .styles-module__settingsLabel___VCVOQ {
  color: rgba(255, 255, 255, 0.2);
}
[data-agentation-theme=light] .styles-module__settingsRowDisabled___ydl3Q .styles-module__settingsLabel___VCVOQ {
  color: rgba(0, 0, 0, 0.2);
}

.styles-module__settingsLabel___VCVOQ {
  display: flex;
  align-items: center;
  column-gap: 2px;
  line-height: 20px;
  font-size: 13px;
  font-weight: 400;
  letter-spacing: -0.15px;
  color: rgba(255, 255, 255, 0.5);
}
[data-agentation-theme=light] .styles-module__settingsLabel___VCVOQ {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__cycleButton___XMBx3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
  border: none;
  background: transparent;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  letter-spacing: -0.0094em;
}
[data-agentation-theme=light] .styles-module__cycleButton___XMBx3 {
  color: rgba(0, 0, 0, 0.85);
}
.styles-module__cycleButton___XMBx3:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.styles-module__cycleButtonText___mbbnD {
  display: inline-block;
  animation: styles-module__cycleTextIn___VBNTi 0.2s ease-out;
}

.styles-module__cycleDots___ehp6i {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.styles-module__cycleDot___zgSXY {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0.667);
  transition: background-color 0.25s ease-out, transform 0.25s ease-out;
}
.styles-module__cycleDot___zgSXY.styles-module__active___dpAhM {
  background: #fff;
  transform: scale(1);
}
[data-agentation-theme=light] .styles-module__cycleDot___zgSXY {
  background: rgba(0, 0, 0, 0.2);
}
[data-agentation-theme=light] .styles-module__cycleDot___zgSXY.styles-module__active___dpAhM {
  background: rgba(0, 0, 0, 0.7);
}

.styles-module__colorOptions___pbxZx {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  height: 26px;
}

.styles-module__colorOption___Co955 {
  padding: 0;
  position: relative;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  background-color: #fff;
  cursor: pointer;
}
[data-agentation-theme=dark] .styles-module__colorOption___Co955 {
  background-color: #1a1a1a;
}
.styles-module__colorOption___Co955::before, .styles-module__colorOption___Co955::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background-color: var(--swatch);
  transition: opacity 0.2s, transform 0.2s;
}
@supports (color: color(display-p3 0 0 0)) {
  .styles-module__colorOption___Co955::before, .styles-module__colorOption___Co955::after {
    --color: var(--swatch-p3);
  }
}
.styles-module__colorOption___Co955::after {
  z-index: -1;
  transform: scale(1.2);
  opacity: 0;
}
.styles-module__colorOption___Co955.styles-module__selected___k1-Vq::before {
  transform: scale(0.8);
}
.styles-module__colorOption___Co955.styles-module__selected___k1-Vq::after {
  opacity: 1;
}

.styles-module__settingsNavLink___uYIwM {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  font-family: inherit;
  line-height: 20px;
  font-size: 13px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.15s ease;
  cursor: pointer;
}
.styles-module__settingsNavLink___uYIwM:hover {
  color: rgba(255, 255, 255, 0.9);
}
.styles-module__settingsNavLink___uYIwM svg {
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.15s ease;
}
.styles-module__settingsNavLink___uYIwM:hover svg {
  color: #fff;
}
[data-agentation-theme=light] .styles-module__settingsNavLink___uYIwM {
  color: rgba(0, 0, 0, 0.5);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___uYIwM:hover {
  color: rgba(0, 0, 0, 0.8);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___uYIwM svg {
  color: rgba(0, 0, 0, 0.25);
}
[data-agentation-theme=light] .styles-module__settingsNavLink___uYIwM:hover svg {
  color: rgba(0, 0, 0, 0.8);
}

.styles-module__settingsNavLinkRight___XBUzC {
  display: flex;
  align-items: center;
  gap: 6px;
}

.styles-module__settingsBackButton___fflll {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  background: transparent;
  font-family: inherit;
  line-height: 20px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: -0.15px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.12s cubic-bezier(0.32, 0.72, 0, 1);
}
.styles-module__settingsBackButton___fflll svg {
  opacity: 0.4;
  flex-shrink: 0;
  transition: opacity 0.15s ease, transform 0.18s cubic-bezier(0.32, 0.72, 0, 1);
}
.styles-module__settingsBackButton___fflll:hover svg {
  opacity: 1;
}
[data-agentation-theme=light] .styles-module__settingsBackButton___fflll {
  color: rgba(0, 0, 0, 0.85);
  border-bottom-color: rgba(0, 0, 0, 0.08);
}

.styles-module__automationHeader___Avra9 {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  font-size: 0.8125rem;
  font-weight: 400;
  color: #fff;
}
[data-agentation-theme=light] .styles-module__automationHeader___Avra9 {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__automationDescription___vFTmJ {
  font-size: 0.6875rem;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
  line-height: 14px;
}
[data-agentation-theme=light] .styles-module__automationDescription___vFTmJ {
  color: rgba(0, 0, 0, 0.5);
}

.styles-module__learnMoreLink___cG7OI {
  color: rgba(255, 255, 255, 0.8);
  text-decoration-line: underline;
  text-decoration-style: dotted;
  text-decoration-color: rgba(255, 255, 255, 0.2);
  text-underline-offset: 2px;
  transition: color 0.15s ease;
}
.styles-module__learnMoreLink___cG7OI:hover {
  color: #fff;
}
[data-agentation-theme=light] .styles-module__learnMoreLink___cG7OI {
  color: rgba(0, 0, 0, 0.6);
  text-decoration-color: rgba(0, 0, 0, 0.2);
}
[data-agentation-theme=light] .styles-module__learnMoreLink___cG7OI:hover {
  color: rgba(0, 0, 0, 0.85);
}

.styles-module__autoSendContainer___VpkXk {
  display: flex;
  align-items: center;
}

.styles-module__autoSendLabel___ngNdC {
  padding-inline-end: 8px;
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.15s, opacity 0.15s;
  cursor: pointer;
}
.styles-module__autoSendLabel___ngNdC.styles-module__active___dpAhM {
  color: #66b8ff;
  color: color(display-p3 0.4 0.72 1);
}
[data-agentation-theme=light] .styles-module__autoSendLabel___ngNdC {
  color: rgba(0, 0, 0, 0.4);
}
[data-agentation-theme=light] .styles-module__autoSendLabel___ngNdC.styles-module__active___dpAhM {
  color: var(--agentation-color-blue);
}
.styles-module__autoSendLabel___ngNdC.styles-module__disabled___9AZYS {
  opacity: 0.3;
  cursor: not-allowed;
}

.styles-module__mcpStatusDot___8AMxP {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.styles-module__mcpStatusDot___8AMxP.styles-module__connecting___QEO1r {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__mcpPulse___5Q3Jj 1.5s infinite;
}
.styles-module__mcpStatusDot___8AMxP.styles-module__connected___WyFkx {
  background-color: var(--agentation-color-green);
  animation: styles-module__mcpPulse___5Q3Jj 2.5s ease-in-out infinite;
}
.styles-module__mcpStatusDot___8AMxP.styles-module__disconnected___mvmvQ {
  background-color: var(--agentation-color-red);
  animation: styles-module__mcpPulseError___VHxhx 2s infinite;
}

.styles-module__mcpNavIndicator___auBHI {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.styles-module__mcpNavIndicator___auBHI.styles-module__connected___WyFkx {
  background-color: var(--agentation-color-green);
  animation: styles-module__mcpPulse___5Q3Jj 2.5s ease-in-out infinite;
}
.styles-module__mcpNavIndicator___auBHI.styles-module__connecting___QEO1r {
  background-color: var(--agentation-color-yellow);
  animation: styles-module__mcpPulse___5Q3Jj 1.5s ease-in-out infinite;
}

.styles-module__webhookUrlInput___WDDDC {
  display: block;
  width: 100%;
  flex: 1;
  min-height: 60px;
  box-sizing: border-box;
  margin-top: 11px;
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: 400;
  color: #fff;
  outline: none;
  resize: none;
  user-select: text;
  transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}
.styles-module__webhookUrlInput___WDDDC::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
.styles-module__webhookUrlInput___WDDDC:focus {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___WDDDC {
  border-color: rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.03);
  color: rgba(0, 0, 0, 0.85);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___WDDDC::placeholder {
  color: rgba(0, 0, 0, 0.3);
}
[data-agentation-theme=light] .styles-module__webhookUrlInput___WDDDC:focus {
  border-color: rgba(0, 0, 0, 0.25);
  background: rgba(0, 0, 0, 0.05);
}

[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn-::before {
  background: linear-gradient(to right, #fff 0%, transparent 100%);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn-::after {
  background: linear-gradient(to left, #fff 0%, transparent 100%);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__settingsHeader___Fn1DP {
  border-bottom-color: rgba(0, 0, 0, 0.08);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__settingsBrand___OoKlM {
  color: #E5484D;
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__settingsVersion___rXmL9 {
  color: rgba(0, 0, 0, 0.4);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__settingsSection___n5V-4 {
  border-top-color: rgba(0, 0, 0, 0.08);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__settingsLabel___VCVOQ {
  color: rgba(0, 0, 0, 0.5);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__cycleButton___XMBx3 {
  color: rgba(0, 0, 0, 0.85);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__cycleDot___zgSXY {
  background: rgba(0, 0, 0, 0.2);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__cycleDot___zgSXY.styles-module__active___dpAhM {
  background: rgba(0, 0, 0, 0.7);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__dropdownButton___mKHe8 {
  color: rgba(0, 0, 0, 0.85);
}
[data-agentation-theme=light] .styles-module__settingsPanel___qNkn- .styles-module__dropdownButton___mKHe8:hover {
  background: rgba(0, 0, 0, 0.05);
}

.styles-module__checkboxField___ZrSqv:not(:first-child) {
  margin-top: 8px;
}

.styles-module__divider___h6Yux {
  margin-block: 8px;
  width: 100%;
  height: 1px;
  background-color: rgba(26, 26, 26, 0.07);
}
[data-agentation-theme=dark] .styles-module__divider___h6Yux {
  background-color: rgba(255, 255, 255, 0.07);
}`,bx={settingsPanel:"styles-module__settingsPanel___qNkn-",settingsHeader:"styles-module__settingsHeader___Fn1DP",settingsBrand:"styles-module__settingsBrand___OoKlM",settingsBrandSlash:"styles-module__settingsBrandSlash___Q-AU9",settingsVersion:"styles-module__settingsVersion___rXmL9",settingsSection:"styles-module__settingsSection___n5V-4",settingsLabel:"styles-module__settingsLabel___VCVOQ",cycleButton:"styles-module__cycleButton___XMBx3",cycleDot:"styles-module__cycleDot___zgSXY",dropdownButton:"styles-module__dropdownButton___mKHe8",sliderLabel:"styles-module__sliderLabel___6K5v1",slider:"styles-module__slider___v5z-c",themeToggle:"styles-module__themeToggle___3imlT",enter:"styles-module__enter___wginS",exit:"styles-module__exit___A4iJc",settingsOption:"styles-module__settingsOption___JoyH-",selected:"styles-module__selected___k1-Vq",settingsPanelContainer:"styles-module__settingsPanelContainer___5it-H",settingsPage:"styles-module__settingsPage___BMn-3",slideLeft:"styles-module__slideLeft___qUvW4",automationsPage:"styles-module__automationsPage___N7By0",slideIn:"styles-module__slideIn___uXDSu",themeIconWrapper:"styles-module__themeIconWrapper___pyaYa",themeIcon:"styles-module__themeIcon___w7lAm",themeIconIn:"styles-module__themeIconIn___qUWMV",settingsSectionGrow:"styles-module__settingsSectionGrow___eZTRw",settingsRow:"styles-module__settingsRow___y-tDE",settingsRowMarginTop:"styles-module__settingsRowMarginTop___uLpGb",settingsRowDisabled:"styles-module__settingsRowDisabled___ydl3Q",cycleButtonText:"styles-module__cycleButtonText___mbbnD",cycleTextIn:"styles-module__cycleTextIn___VBNTi",cycleDots:"styles-module__cycleDots___ehp6i",active:"styles-module__active___dpAhM",colorOptions:"styles-module__colorOptions___pbxZx",colorOption:"styles-module__colorOption___Co955",settingsNavLink:"styles-module__settingsNavLink___uYIwM",settingsNavLinkRight:"styles-module__settingsNavLinkRight___XBUzC",settingsBackButton:"styles-module__settingsBackButton___fflll",automationHeader:"styles-module__automationHeader___Avra9",automationDescription:"styles-module__automationDescription___vFTmJ",learnMoreLink:"styles-module__learnMoreLink___cG7OI",autoSendContainer:"styles-module__autoSendContainer___VpkXk",autoSendLabel:"styles-module__autoSendLabel___ngNdC",disabled:"styles-module__disabled___9AZYS",mcpStatusDot:"styles-module__mcpStatusDot___8AMxP",connecting:"styles-module__connecting___QEO1r",mcpPulse:"styles-module__mcpPulse___5Q3Jj",connected:"styles-module__connected___WyFkx",disconnected:"styles-module__disconnected___mvmvQ",mcpPulseError:"styles-module__mcpPulseError___VHxhx",mcpNavIndicator:"styles-module__mcpNavIndicator___auBHI",webhookUrlInput:"styles-module__webhookUrlInput___WDDDC",checkboxField:"styles-module__checkboxField___ZrSqv",divider:"styles-module__divider___h6Yux",scaleIn:"styles-module__scaleIn___QpQ8E"};if(typeof document<"u"){let e=document.getElementById("feedback-tool-styles-settings-panel-styles");e||(e=document.createElement("style"),e.id="feedback-tool-styles-settings-panel-styles",document.head.appendChild(e)),e.textContent=wx}var oe=bx;function kx({settings:e,onSettingsChange:t,isDarkMode:n,onToggleTheme:o,isDevMode:r,connectionStatus:l,endpoint:i,isVisible:s,toolbarNearBottom:a,settingsPage:m,onSettingsPageChange:p,onHideToolbar:b}){return(0,G.jsx)("div",{className:`${oe.settingsPanel} ${s?oe.enter:oe.exit}`,style:a?{bottom:"auto",top:"calc(100% + 0.5rem)"}:void 0,"data-agentation-settings-panel":!0,children:(0,G.jsxs)("div",{className:oe.settingsPanelContainer,children:[(0,G.jsxs)("div",{className:`${oe.settingsPage} ${m==="automations"?oe.slideLeft:""}`,children:[(0,G.jsxs)("div",{className:oe.settingsHeader,children:[(0,G.jsx)("a",{className:oe.settingsBrand,href:"https://agentation.com",target:"_blank",rel:"noopener noreferrer",children:(0,G.jsx)("svg",{width:"72",height:"16",viewBox:"0 0 676 151",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,G.jsx)("path",{d:"M79.6666 100.561L104.863 15.5213C107.828 4.03448 99.1201 -3.00582 88.7449 1.25541L3.52015 39.6065C1.48217 40.5329 0 42.7562 0 45.1647C0 48.6848 2.77907 51.4639 6.29922 51.4639C7.22558 51.4639 8.15193 51.2786 9.07829 50.9081L93.7472 12.7422C97.2674 11.0748 93.7472 8.29572 92.6356 12.1864L67.624 97.2259C66.5123 100.931 69.4767 105.193 73.7379 105.193C76.517 105.193 79.1108 103.155 79.6666 100.561ZM663.641 100.005C665.679 107.231 677.537 104.081 675.499 96.8553L666.05 66.2856C663.456 57.7631 655.489 55.7251 648.82 61.098L618.991 86.6654C617.324 87.9623 621.029 89.815 621.214 88.1476L625.846 61.6538C626.958 55.3546 624.179 50.5375 615.841 50.5375L579.158 51.0934C576.008 51.0934 578.417 53.8724 578.417 57.022C578.417 60.1716 580.825 61.6538 583.975 61.6538L616.212 60.9127C616.397 60.9127 614.544 59.6158 614.544 59.8011L609.727 88.7034C607.875 99.6344 617.694 102.784 626.031 95.7437L655.86 70.1763L654.192 69.6205L663.641 100.005ZM571.191 89.0739C555.443 88.7034 562.298 61.4685 578.787 61.8391C594.72 62.0243 587.124 89.2592 571.191 89.0739ZM571.006 100.375C601.575 100.931 611.024 51.6492 579.158 51.0934C547.847 50.5375 540.065 99.8197 571.006 100.375ZM521.909 46.4616C525.985 46.4616 529.505 42.9414 529.505 38.6802C529.505 34.4189 525.985 31.0841 521.909 31.0841C517.833 31.0841 514.127 34.6042 514.127 38.6802C514.127 42.7562 517.648 46.4616 521.909 46.4616ZM472.256 103.525C493.192 103.71 515.98 73.3259 519.13 62.3949L509.866 60.9127C505.234 73.3259 497.638 101.672 519.871 102.043C536.545 102.228 552.479 85.3685 563.595 70.1763C564.151 69.2499 564.706 68.1383 564.706 66.8414C564.706 63.6918 563.965 61.098 560.816 61.098C558.963 61.098 557.296 62.0243 556.184 63.5065C546.365 77.0313 530.802 90.9266 522.094 90.7414C511.904 90.5561 517.462 71.4732 519.871 64.9887C523.391 55.7251 512.831 53.5019 509.681 60.9127C506.531 68.6941 488.19 92.4088 475.035 92.2235C467.439 92.0383 464.29 83.8863 472.441 59.9864L486.707 17.7445C487.634 14.4097 485.41 10.519 481.334 10.519C478.741 10.519 476.517 12.1864 475.962 14.4097L461.696 56.4662C451.506 86.4801 455.211 103.155 472.256 103.525ZM447.43 42.5709L496.527 41.4593C499.306 41.4593 501.529 39.0507 501.529 36.2717C501.529 33.3073 499.306 31.0841 496.341 31.0841L447.245 32.1957C444.466 32.1957 442.242 34.4189 442.242 37.3833C442.242 40.1624 444.466 42.5709 447.43 42.5709ZM422.974 106.304C435.387 106.489 457.249 94.8173 472.441 53.8724C473.553 50.7228 472.071 48.3143 468.365 48.3143C466.142 48.3143 464.29 49.6112 463.548 51.6492C450.394 87.2212 431.682 96.1142 424.456 95.929C419.454 95.929 417.972 93.3352 418.713 85.5538C419.454 78.1429 410.376 74.9933 406.114 81.1073C401.297 87.777 394.442 94.2615 385.549 94.0763C370.172 93.891 376.471 67.0267 399.815 67.3972C408.338 67.5825 414.452 71.4732 417.045 76.6608C417.786 78.3282 419.454 79.6251 421.492 79.6251C424.271 79.6251 426.679 77.2166 426.679 74.4375C426.679 73.6964 426.494 72.9553 426.124 72.2143C421.862 63.6918 412.414 57.3926 400 57.2073C363.502 56.6515 353.497 104.451 383.326 104.822C397.036 105.193 410.005 94.0763 413.34 85.9243C412.599 86.8507 408.338 86.6654 408.523 84.4422C407.411 97.4111 410.931 106.119 422.974 106.304ZM335.897 104.266C335.897 115.012 347.569 117.606 347.569 103.34C347.569 89.0739 358.5 54.4282 361.464 45.1647L396.666 43.6825C405.929 43.1267 404.262 33.1221 397.036 33.3073L364.984 34.4189L368.875 22.7469C369.801 20.1531 370.542 17.9298 370.542 16.2624C370.542 13.4833 368.504 11.8159 365.911 11.8159C362.946 11.8159 360.352 12.7422 357.573 21.0794L352.942 35.16L330.153 36.0864C326.263 36.4569 323.483 38.1244 323.483 41.6445C323.483 45.5352 326.448 47.0174 330.709 46.8321L349.421 45.9058C345.901 56.6515 335.897 90.7414 335.897 104.266ZM186.939 78.6988C193.979 56.4662 212.877 54.984 212.877 62.9507C212.877 68.3236 203.984 77.0313 186.939 78.6988ZM113.942 150.955C142.844 152.437 159.704 111.492 160.63 80.5515C161.556 73.3259 153.96 70.3616 148.773 75.7344C141.918 83.1453 129.505 93.1499 119.685 93.1499C103.011 93.1499 116.165 59.8011 143.956 59.8011C149.514 59.8011 153.59 61.6538 156.184 64.0623C160.815 68.3236 170.82 62.0243 165.818 56.0957C161.927 51.4639 155.072 48.129 144.882 48.129C102.455 48.129 83.7426 105.007 116.721 105.007C134.692 105.007 151.367 88.3329 155.257 82.7747C154.516 83.5158 149.329 81.2925 149.699 79.4398L149.143 83.5158C148.958 107.045 134.322 141.506 116.536 139.838C113.386 139.468 112.089 137.43 112.089 134.836C112.089 128.907 122.094 119.273 145.067 113.53C159.518 109.824 152.293 101.487 143.4 104.081C111.163 113.53 99.6759 127.425 99.6759 137.8C99.6759 145.026 105.605 150.584 113.942 150.955ZM194.72 109.454C214.359 109.454 239 95.3732 251.228 77.9577C250.301 82.96 246.596 96.8553 246.596 101.487C246.596 110.01 254.748 109.454 261.232 102.784L288.097 75.5491L290.32 85.7391C293.284 99.4491 299.213 104.822 308.847 104.822C326.263 104.822 342.196 85.7391 349.421 74.8081L344.049 63.6918C339.787 74.8081 321.631 92.5941 311.626 92.5941C306.994 92.5941 304.771 89.815 303.289 83.7011L300.325 71.2879C297.916 60.7275 289.023 58.3189 279.018 68.1383L261.788 84.8127L264.382 69.991C266.235 59.2453 255.674 58.1337 250.116 65.915C241.779 77.0313 216.767 97.7817 196.387 97.7817C187.865 97.7817 185.456 93.7057 185.456 88.3329C230.848 84.998 239.185 47.2027 208.986 47.2027C172.858 47.2027 157.11 109.454 194.72 109.454Z",fill:"currentColor"})})}),(0,G.jsxs)("p",{className:oe.settingsVersion,children:["v","3.0.2"]}),(0,G.jsx)("button",{className:oe.themeToggle,onClick:o,title:n?"Switch to light mode":"Switch to dark mode",children:(0,G.jsx)("span",{className:oe.themeIconWrapper,children:(0,G.jsx)("span",{className:oe.themeIcon,children:n?(0,G.jsx)(Pp,{size:20}):(0,G.jsx)(Tp,{size:20})},n?"sun":"moon")})})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("div",{className:oe.settingsSection,children:[(0,G.jsxs)("div",{className:oe.settingsRow,children:[(0,G.jsxs)("div",{className:oe.settingsLabel,children:["Output Detail",(0,G.jsx)(Nr,{content:"Controls how much detail is included in the copied output"})]}),(0,G.jsxs)("button",{className:oe.cycleButton,onClick:()=>{let R=(Pi.findIndex(C=>C.value===e.outputDetail)+1)%Pi.length;t({outputDetail:Pi[R].value})},children:[(0,G.jsx)("span",{className:oe.cycleButtonText,children:Pi.find(y=>y.value===e.outputDetail)?.label},e.outputDetail),(0,G.jsx)("span",{className:oe.cycleDots,children:Pi.map(y=>(0,G.jsx)("span",{className:`${oe.cycleDot} ${e.outputDetail===y.value?oe.active:""}`},y.value))})]})]}),(0,G.jsxs)("div",{className:`${oe.settingsRow} ${oe.settingsRowMarginTop} ${r?"":oe.settingsRowDisabled}`,children:[(0,G.jsxs)("div",{className:oe.settingsLabel,children:["React Components",(0,G.jsx)(Nr,{content:r?"Include React component names in annotations":"Disabled \u2014 production builds minify component names, making detection unreliable. Use in development mode."})]}),(0,G.jsx)(Cu,{checked:r&&e.reactEnabled,onChange:y=>t({reactEnabled:y.target.checked}),disabled:!r})]}),(0,G.jsxs)("div",{className:`${oe.settingsRow} ${oe.settingsRowMarginTop}`,children:[(0,G.jsxs)("div",{className:oe.settingsLabel,children:["Hide Until Restart",(0,G.jsx)(Nr,{content:"Hides the toolbar until you open a new tab"})]}),(0,G.jsx)(Cu,{checked:!1,onChange:y=>{y.target.checked&&b()}})]})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("div",{className:oe.settingsSection,children:[(0,G.jsx)("div",{className:`${oe.settingsLabel} ${oe.settingsLabelMarker}`,children:"Marker Color"}),(0,G.jsx)("div",{className:oe.colorOptions,children:Ti.map(y=>(0,G.jsx)("button",{className:`${oe.colorOption} ${e.annotationColorId===y.id?oe.selected:""}`,style:{"--swatch":y.srgb,"--swatch-p3":y.p3},onClick:()=>t({annotationColorId:y.id}),title:y.label,type:"button"},y.id))})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("div",{className:oe.settingsSection,children:[(0,G.jsx)(vp,{className:"checkbox-field",label:"Clear on copy/send",checked:e.autoClearAfterCopy,onChange:y=>t({autoClearAfterCopy:y.target.checked}),tooltip:"Automatically clear annotations after copying"}),(0,G.jsx)(vp,{className:oe.checkboxField,label:"Block page interactions",checked:e.blockInteractions,onChange:y=>t({blockInteractions:y.target.checked})})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("button",{className:oe.settingsNavLink,onClick:()=>p("automations"),children:[(0,G.jsx)("span",{children:"Manage MCP & Webhooks"}),(0,G.jsxs)("span",{className:oe.settingsNavLinkRight,children:[i&&l!=="disconnected"&&(0,G.jsx)("span",{className:`${oe.mcpNavIndicator} ${oe[l]}`}),(0,G.jsx)("svg",{width:"16",height:"16",viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:(0,G.jsx)("path",{d:"M7.5 12.5L12 8L7.5 3.5",stroke:"currentColor",strokeWidth:"1.5",strokeLinecap:"round",strokeLinejoin:"round"})})]})]})]}),(0,G.jsxs)("div",{className:`${oe.settingsPage} ${oe.automationsPage} ${m==="automations"?oe.slideIn:""}`,children:[(0,G.jsxs)("button",{className:oe.settingsBackButton,onClick:()=>p("main"),children:[(0,G.jsx)(zp,{size:16}),(0,G.jsx)("span",{children:"Manage MCP & Webhooks"})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("div",{className:oe.settingsSection,children:[(0,G.jsxs)("div",{className:oe.settingsRow,children:[(0,G.jsxs)("span",{className:oe.automationHeader,children:["MCP Connection",(0,G.jsx)(Nr,{content:"Connect via Model Context Protocol to let AI agents like Claude Code receive annotations in real-time."})]}),i&&(0,G.jsx)("div",{className:`${oe.mcpStatusDot} ${oe[l]}`,title:l==="connected"?"Connected":l==="connecting"?"Connecting...":"Disconnected"})]}),(0,G.jsxs)("p",{className:oe.automationDescription,style:{paddingBottom:6},children:["MCP connection allows agents to receive and act on annotations."," ",(0,G.jsx)("a",{href:"https://agentation.dev/mcp",target:"_blank",rel:"noopener noreferrer",className:oe.learnMoreLink,children:"Learn more"})]})]}),(0,G.jsx)("div",{className:oe.divider}),(0,G.jsxs)("div",{className:`${oe.settingsSection} ${oe.settingsSectionGrow}`,children:[(0,G.jsxs)("div",{className:oe.settingsRow,children:[(0,G.jsxs)("span",{className:oe.automationHeader,children:["Webhooks",(0,G.jsx)(Nr,{content:"Send annotation data to any URL endpoint when annotations change. Useful for custom integrations."})]}),(0,G.jsxs)("div",{className:oe.autoSendContainer,children:[(0,G.jsx)("label",{htmlFor:"agentation-auto-send",className:`${oe.autoSendLabel} ${e.webhooksEnabled?oe.active:""} ${e.webhookUrl?"":oe.disabled}`,children:"Auto-Send"}),(0,G.jsx)(Cu,{id:"agentation-auto-send",checked:e.webhooksEnabled,onChange:y=>t({webhooksEnabled:y.target.checked}),disabled:!e.webhookUrl})]})]}),(0,G.jsx)("p",{className:oe.automationDescription,children:"The webhook URL will receive live annotation changes and annotation data."}),(0,G.jsx)("textarea",{className:oe.webhookUrlInput,placeholder:"Webhook URL",value:e.webhookUrl,onKeyDown:y=>y.stopPropagation(),onChange:y=>t({webhookUrl:y.target.value})})]})]})]})})}function Su(e,t="filtered"){let{name:n,path:o}=$r(e);if(t==="off")return{name:n,elementName:n,path:o,reactComponents:null};let r=G2(e,{mode:t});return{name:r.path?`${r.path} ${n}`:n,elementName:n,path:o,reactComponents:r.path}}var wp=!1,Mu={outputDetail:"standard",autoClearAfterCopy:!1,annotationColorId:"blue",blockInteractions:!0,reactEnabled:!0,markerClickBehavior:"edit",webhookUrl:"",webhooksEnabled:!0},ho=e=>{if(!e||!e.trim())return!1;try{let t=new URL(e.trim());return t.protocol==="http:"||t.protocol==="https:"}catch{return!1}},Cx={compact:"off",standard:"filtered",detailed:"smart",forensic:"all"},Ti=[{id:"indigo",label:"Indigo",srgb:"#6155F5",p3:"color(display-p3 0.38 0.33 0.96)"},{id:"blue",label:"Blue",srgb:"#0088FF",p3:"color(display-p3 0.00 0.53 1.00)"},{id:"cyan",label:"Cyan",srgb:"#00C3D0",p3:"color(display-p3 0.00 0.76 0.82)"},{id:"green",label:"Green",srgb:"#34C759",p3:"color(display-p3 0.20 0.78 0.35)"},{id:"yellow",label:"Yellow",srgb:"#FFCC00",p3:"color(display-p3 1.00 0.80 0.00)"},{id:"orange",label:"Orange",srgb:"#FF8D28",p3:"color(display-p3 1.00 0.55 0.16)"},{id:"red",label:"Red",srgb:"#FF383C",p3:"color(display-p3 1.00 0.22 0.24)"}],Sx=()=>{if(typeof document>"u"||document.getElementById("agentation-color-tokens"))return;let e=document.createElement("style");e.id="agentation-color-tokens",e.textContent=[...Ti.map(t=>`
      [data-agentation-accent="${t.id}"] {
        --agentation-color-accent: ${t.srgb};
      }

      @supports (color: color(display-p3 0 0 0)) {
        [data-agentation-accent="${t.id}"] {
          --agentation-color-accent: ${t.p3};
        }
      }
    `),`:root {
      ${Ti.map(t=>`--agentation-color-${t.id}: ${t.srgb};`).join(`
`)}
    }`,`@supports (color: color(display-p3 0 0 0)) {
      :root {
        ${Ti.map(t=>`--agentation-color-${t.id}: ${t.p3};`).join(`
`)}
      }
    }`].join(""),document.head.appendChild(e)};Sx();function Lr(e,t){let n=document.elementFromPoint(e,t);if(!n)return null;for(;n?.shadowRoot;){let o=n.shadowRoot.elementFromPoint(e,t);if(!o||o===n)break;n=o}return n}function Eu(e){let t=e;for(;t&&t!==document.body;){let o=window.getComputedStyle(t).position;if(o==="fixed"||o==="sticky")return!0;t=t.parentElement}return!1}function Ir(e){return e.status!=="resolved"&&e.status!=="dismissed"}function Ra(e){let t=Du(e),n=t.found?t:ax(e);if(n.found&&n.source)return sx(n.source,"path")}function Mx({demoAnnotations:e,demoDelay:t=1e3,enableDemoMode:n=!1,onAnnotationAdd:o,onAnnotationDelete:r,onAnnotationUpdate:l,onAnnotationsClear:i,onCopy:s,onSubmit:a,copyToClipboard:m=!0,endpoint:p,sessionId:b,onSessionCreated:y,webhookUrl:R,className:C}={}){let[N,L]=(0,M.useState)(!1),[f,g]=(0,M.useState)([]),[w,$]=(0,M.useState)(!0),[U,V]=(0,M.useState)(()=>z2()),[B,q]=(0,M.useState)(!1),ye=(0,M.useRef)(null);(0,M.useEffect)(()=>{let u=x=>{let v=ye.current;v&&v.contains(x.target)&&x.stopPropagation()},h=["mousedown","click","pointerdown"];return h.forEach(x=>document.body.addEventListener(x,u)),()=>{h.forEach(x=>document.body.removeEventListener(x,u))}},[]);let[Z,he]=(0,M.useState)(!1),[Ge,st]=(0,M.useState)(!1),[Re,We]=(0,M.useState)(null),[Ee,qe]=(0,M.useState)({x:0,y:0}),[Q,me]=(0,M.useState)(null),[Ye,Mt]=(0,M.useState)(!1),[cn,tn]=(0,M.useState)("idle"),[$o,Sn]=(0,M.useState)(!1),[Ro,On]=(0,M.useState)(!1),[mo,Po]=(0,M.useState)(null),[rr,gn]=(0,M.useState)(null),[An,dn]=(0,M.useState)([]),[eo,to]=(0,M.useState)(null),[Tr,Wn]=(0,M.useState)(null),[Pe,Y]=(0,M.useState)(null),[ue,xe]=(0,M.useState)(null),[$e,ve]=(0,M.useState)([]),[Ze,tt]=(0,M.useState)(0),[Xe,ze]=(0,M.useState)(!1),[pe,S]=(0,M.useState)(!1),[I,z]=(0,M.useState)(!1),[A,J]=(0,M.useState)(!1),[le,j]=(0,M.useState)(!1),[ie,Se]=(0,M.useState)("main"),[Fe,Je]=(0,M.useState)(!1),[se,nt]=(0,M.useState)(!1),[Te,Le]=(0,M.useState)(!1),[ae,ot]=(0,M.useState)([]),[je,Ie]=(0,M.useState)(null),Qe=(0,M.useRef)(!1),[we,ut]=(0,M.useState)(!1),[Ft,Mn]=(0,M.useState)(!1),[no,un]=(0,M.useState)(1),[go,Ai]=(0,M.useState)("new-page"),[It,yo]=(0,M.useState)(""),[Wi,om]=(0,M.useState)(!1),[Ce,En]=(0,M.useState)(null),Da=(0,M.useRef)(!1),Ba=(0,M.useRef)({rearrange:null,placements:[]}),lr=(0,M.useRef)({rearrange:null,placements:[]}),[rm,ju]=(0,M.useState)(0),[lm,im]=(0,M.useState)(0),[sm,za]=(0,M.useState)(0),[am,Hu]=(0,M.useState)(0),El=(0,M.useRef)(new Set),Fi=(0,M.useRef)(new Set),Fn=(0,M.useRef)(null),ji=(0,M.useRef)(),Uu=se&&N&&!Te&&we;(0,M.useEffect)(()=>{if(Uu){Mn(!1);let u=kl(()=>{Mn(!0)});return()=>cancelAnimationFrame(u)}else Mn(!1)},[Uu]);let Ll=(0,M.useRef)(new Map),Il=(0,M.useRef)(new Map),Nl=(0,M.useRef)(),[jn,Oa]=(0,M.useState)(!1),[Ln,cm]=(0,M.useState)([]),dm=(0,M.useRef)(Ln);dm.current=Ln;let[Yu,Ex]=(0,M.useState)(null),Aa=(0,M.useRef)(null),Lx=(0,M.useRef)(!1),Ix=(0,M.useRef)([]),Nx=(0,M.useRef)(0),$x=(0,M.useRef)(null),Rx=(0,M.useRef)(null),Px=(0,M.useRef)(1),[Xu,Qu]=(0,M.useState)(!1),Dr=(0,M.useRef)(null),[Tt,Br]=(0,M.useState)([]),oo=(0,M.useRef)({cmd:!1,shift:!1}),Vt=()=>{Je(!0)},um=()=>{Je(!1)},_m=()=>{Xu||(Dr.current=fe(()=>Qu(!0),850))},fm=()=>{Dr.current&&(clearTimeout(Dr.current),Dr.current=null),Qu(!1),um()};(0,M.useEffect)(()=>()=>{Dr.current&&clearTimeout(Dr.current)},[]);let[De,hm]=(0,M.useState)(()=>{try{let u=JSON.parse(localStorage.getItem("feedback-toolbar-settings")??"");return{...Mu,...u,annotationColorId:Ti.find(h=>h.id===u.annotationColorId)?u.annotationColorId:Mu.annotationColorId}}catch{return Mu}}),[ro,Vu]=(0,M.useState)(!0),[Ku,qu]=(0,M.useState)(!1),pm=()=>{ye.current?.classList.add(W.disableTransitions),Vu(u=>!u),kl(()=>{ye.current?.classList.remove(W.disableTransitions)})},Gu=!1,ir=Gu&&De.reactEnabled?Cx[De.outputDetail]:"off",[zt,Wa]=(0,M.useState)(b??null),Zu=(0,M.useRef)(!1),[Hn,sr]=(0,M.useState)(p?"connecting":"disconnected"),[xt,Fa]=(0,M.useState)(null),[ar,Ju]=(0,M.useState)(!1),[zr,e_]=(0,M.useState)(null),ja=(0,M.useRef)(!1),[t_,$l]=(0,M.useState)(new Set),[n_,Hi]=(0,M.useState)(new Set),[Rl,Ui]=(0,M.useState)(!1),[mm,Or]=(0,M.useState)(!1),[xo,o_]=(0,M.useState)(!1),Ar=(0,M.useRef)(null),lo=(0,M.useRef)(null),Pl=(0,M.useRef)(null),Tl=(0,M.useRef)(null),Yi=(0,M.useRef)(!1),r_=(0,M.useRef)(0),Xi=(0,M.useRef)(null),l_=(0,M.useRef)(null),Ha=8,gm=50,i_=(0,M.useRef)(null),s_=(0,M.useRef)(null),Dl=(0,M.useRef)(null),ge=typeof window<"u"?window.location.pathname:"/";(0,M.useEffect)(()=>{if(A)j(!0);else{Je(!1),Se("main");let u=fe(()=>j(!1),0);return()=>clearTimeout(u)}},[A]);let Ua=N&&w&&!se;(0,M.useEffect)(()=>{if(Ua){st(!1),he(!0),$l(new Set);let u=fe(()=>{$l(h=>{let x=new Set(h);return f.forEach(v=>x.add(v.id)),x})},350);return()=>clearTimeout(u)}else if(Z){st(!0);let u=fe(()=>{he(!1),st(!1)},250);return()=>clearTimeout(u)}},[Ua]),(0,M.useEffect)(()=>{S(!0),tt(window.scrollY);let u=Pa(ge);g(u.filter(Ir)),wp||(qu(!0),wp=!0,fe(()=>qu(!1),750));try{let h=localStorage.getItem("feedback-toolbar-theme");h!==null&&Vu(h==="dark")}catch{}try{let h=localStorage.getItem("feedback-toolbar-position");if(h){let x=JSON.parse(h);typeof x.x=="number"&&typeof x.y=="number"&&Fa(x)}}catch{}},[ge]),(0,M.useEffect)(()=>{pe&&localStorage.setItem("feedback-toolbar-settings",JSON.stringify(De))},[De,pe]),(0,M.useEffect)(()=>{pe&&localStorage.setItem("feedback-toolbar-theme",ro?"dark":"light")},[ro,pe]);let a_=(0,M.useRef)(!1);(0,M.useEffect)(()=>{let u=a_.current;a_.current=ar,u&&!ar&&xt&&pe&&localStorage.setItem("feedback-toolbar-position",JSON.stringify(xt))},[ar,xt,pe]),(0,M.useEffect)(()=>{if(!p||!pe||Zu.current)return;Zu.current=!0,sr("connecting"),(async()=>{try{let h=D2(ge),x=b||h,v=!1;if(x)try{let k=await _p(p,x);Wa(k.id),sr("connected"),vu(ge,k.id),v=!0;let D=Pa(ge),X=new Set(k.annotations.map(re=>re.id)),K=D.filter(re=>!X.has(re.id));if(K.length>0){let ce=`${typeof window<"u"?window.location.origin:""}${ge}`,Me=(await Promise.allSettled(K.map(_e=>xl(p,k.id,{..._e,sessionId:k.id,url:ce})))).map((_e,te)=>_e.status==="fulfilled"?_e.value:(console.warn("[Agentation] Failed to sync annotation:",_e.reason),K[te])),Oe=[...k.annotations,...Me];g(Oe.filter(Ir)),Ni(ge,Oe.filter(Ir),k.id)}else g(k.annotations.filter(Ir)),Ni(ge,k.annotations.filter(Ir),k.id)}catch(k){console.warn("[Agentation] Could not join session, creating new:",k),B2(ge)}if(!v){let k=typeof window<"u"?window.location.href:"/",D=await wu(p,k);Wa(D.id),sr("connected"),vu(ge,D.id),y?.(D.id);let X=E2(),K=typeof window<"u"?window.location.origin:"",re=[];for(let[ce,de]of X){let Me=de.filter(te=>!te._syncedTo);if(Me.length===0)continue;let Oe=`${K}${ce}`,_e=ce===ge;re.push((async()=>{try{let te=_e?D:await wu(p,Oe),Ot=(await Promise.allSettled(Me.map(rt=>xl(p,te.id,{...rt,sessionId:te.id,url:Oe})))).map((rt,$t)=>rt.status==="fulfilled"?rt.value:(console.warn("[Agentation] Failed to sync annotation:",rt.reason),Me[$t])).filter(Ir);if(Ni(ce,Ot,te.id),_e){let rt=new Set(Me.map($t=>$t.id));g($t=>{let be=$t.filter(Ne=>!rt.has(Ne.id));return[...Ot,...be]})}}catch(te){console.warn(`[Agentation] Failed to sync annotations for ${ce}:`,te)}})())}await Promise.allSettled(re)}}catch(h){sr("disconnected"),console.warn("[Agentation] Failed to initialize session, using local storage:",h)}})()},[p,b,pe,y,ge]),(0,M.useEffect)(()=>{if(!p||!pe)return;let u=async()=>{try{(await fetch(`${p}/health`)).ok?sr("connected"):sr("disconnected")}catch{sr("disconnected")}};u();let h=Ly(u,1e4);return()=>clearInterval(h)},[p,pe]),(0,M.useEffect)(()=>{if(!p||!pe||!zt)return;let u=new EventSource(`${p}/sessions/${zt}/events`),h=["resolved","dismissed"],x=v=>{try{let k=JSON.parse(v.data);if(h.includes(k.payload?.status)){let D=k.payload.id,X=k.payload.kind;if(X==="placement"){for(let[K,re]of Ll.current)if(re===D){Ll.current.delete(K),ot(ce=>ce.filter(de=>de.id!==K));break}}else if(X==="rearrange"){for(let[K,re]of Il.current)if(re===D){Il.current.delete(K),En(ce=>{if(!ce)return null;let de=ce.sections.filter(Me=>Me.id!==K);return de.length===0?null:{...ce,sections:de}});break}}else Hi(K=>new Set(K).add(D)),fe(()=>{g(K=>K.filter(re=>re.id!==D)),Hi(K=>{let re=new Set(K);return re.delete(D),re})},150)}}catch{}};return u.addEventListener("annotation.updated",x),()=>{u.removeEventListener("annotation.updated",x),u.close()}},[p,pe,zt]),(0,M.useEffect)(()=>{if(!p||!pe)return;let u=l_.current==="disconnected",h=Hn==="connected";l_.current=Hn,u&&h&&(async()=>{try{let v=Pa(ge);if(v.length===0)return;let D=`${typeof window<"u"?window.location.origin:""}${ge}`,X=zt,K=[];if(X)try{K=(await _p(p,X)).annotations}catch{X=null}X||(X=(await wu(p,D)).id,Wa(X),vu(ge,X));let re=new Set(K.map(de=>de.id)),ce=v.filter(de=>!re.has(de.id));if(ce.length>0){let Me=(await Promise.allSettled(ce.map(te=>xl(p,X,{...te,sessionId:X,url:D})))).map((te,Nt)=>te.status==="fulfilled"?te.value:(console.warn("[Agentation] Failed to sync annotation on reconnect:",te.reason),ce[Nt])),_e=[...K,...Me].filter(Ir);g(_e),Ni(ge,_e,X)}}catch(v){console.warn("[Agentation] Failed to sync on reconnect:",v)}})()},[Hn,p,pe,zt,ge]);let ym=(0,M.useCallback)(()=>{B||(q(!0),J(!1),L(!1),fe(()=>{O2(!0),V(!0),q(!1)},400))},[B]);(0,M.useEffect)(()=>{if(!n||!pe||!e||e.length===0||f.length>0)return;let u=[];return u.push(fe(()=>{L(!0)},t-200)),e.forEach((h,x)=>{let v=t+x*300;u.push(fe(()=>{let k=document.querySelector(h.selector);if(!k)return;let D=k.getBoundingClientRect(),{name:X,path:K}=$r(k),re={id:`demo-${Date.now()}-${x}`,x:(D.left+D.width/2)/window.innerWidth*100,y:D.top+D.height/2+window.scrollY,comment:h.comment,element:X,elementPath:K,timestamp:Date.now(),selectedText:h.selectedText,boundingBox:{x:D.left,y:D.top+window.scrollY,width:D.width,height:D.height},nearbyText:wl(k),cssClasses:bl(k)};g(ce=>[...ce,re])},v))}),()=>{u.forEach(clearTimeout)}},[n,pe,e,t]),(0,M.useEffect)(()=>{let u=()=>{tt(window.scrollY),ze(!0),Dl.current&&clearTimeout(Dl.current),Dl.current=fe(()=>{ze(!1)},150)};return window.addEventListener("scroll",u,{passive:!0}),()=>{window.removeEventListener("scroll",u),Dl.current&&clearTimeout(Dl.current)}},[]),(0,M.useEffect)(()=>{pe&&f.length>0?zt?Ni(ge,f,zt):zu(ge,f):pe&&f.length===0&&localStorage.removeItem(Bi(ge))},[f,ge,pe,zt]),(0,M.useEffect)(()=>{if(pe&&!Qe.current){Qe.current=!0;let u=L2(ge);u.length>0&&ot(u)}},[pe,ge]),(0,M.useEffect)(()=>{pe&&Qe.current&&!we&&(ae.length>0?I2(ge,ae):N2(ge))},[ae,ge,pe,we]),(0,M.useEffect)(()=>{if(pe&&!Da.current){Da.current=!0;let u=$2(ge);if(u){let h={...u,sections:u.sections.map(x=>({...x,currentRect:x.currentRect??{...x.originalRect}}))};En(h)}}},[pe,ge]),(0,M.useEffect)(()=>{pe&&Da.current&&!we&&(Ce?R2(ge,Ce):P2(ge))},[Ce,ge,pe,we]);let Ya=(0,M.useRef)(!1);(0,M.useEffect)(()=>{if(pe&&!Ya.current){Ya.current=!0;let u=T2(ge);u&&(lr.current={rearrange:u.rearrange,placements:u.placements||[]},u.purpose&&yo(u.purpose))}},[pe,ge]),(0,M.useEffect)(()=>{if(!pe||!Ya.current)return;let u=lr.current;we?(Ce?.sections?.length??0)>0||ae.length>0||It?up(ge,{rearrange:Ce,placements:ae,purpose:It}):Ia(ge):(u.rearrange?.sections?.length??0)>0||u.placements.length>0||It?up(ge,{rearrange:u.rearrange,placements:u.placements,purpose:It}):Ia(ge)},[Ce,ae,It,we,ge,pe]),(0,M.useEffect)(()=>{se&&!Ce&&En({sections:[],originalOrder:[],detectedAt:Date.now()})},[se,Ce]),(0,M.useEffect)(()=>{if(!p||!zt)return;let u=Ll.current,h=new Set(ae.map(x=>x.id));for(let x of ae){if(u.has(x.id))continue;u.set(x.id,"");let v=typeof window<"u"?window.location.pathname+window.location.search+window.location.hash:ge;xl(p,zt,{id:x.id,x:x.x/window.innerWidth*100,y:x.y,comment:`Place ${x.type} at (${Math.round(x.x)}, ${Math.round(x.y)}), ${x.width}\xD7${x.height}px${x.text?` \u2014 "${x.text}"`:""}`,element:`[design:${x.type}]`,elementPath:"[placement]",timestamp:x.timestamp,url:v,intent:"change",severity:"important",kind:"placement",placement:{componentType:x.type,width:x.width,height:x.height,scrollY:x.scrollY,text:x.text}}).then(k=>{u.has(x.id)&&u.set(x.id,k.id)}).catch(k=>{console.warn("[Agentation] Failed to sync placement annotation:",k),u.delete(x.id)})}for(let[x,v]of u)h.has(x)||(u.delete(x),v&&or(p,v).catch(()=>{}))},[ae,p,zt,ge]),(0,M.useEffect)(()=>{if(!(!p||!zt))return Nl.current&&clearTimeout(Nl.current),Nl.current=fe(()=>{let u=Il.current;if(!Ce||Ce.sections.length===0){for(let[,v]of u)v&&or(p,v).catch(()=>{});u.clear();return}let h=new Set(Ce.sections.map(v=>v.id)),x=typeof window<"u"?window.location.pathname+window.location.search+window.location.hash:ge;for(let v of Ce.sections){let k=v.originalRect,D=v.currentRect;if(!(Math.abs(k.x-D.x)>1||Math.abs(k.y-D.y)>1||Math.abs(k.width-D.width)>1||Math.abs(k.height-D.height)>1)){let re=u.get(v.id);re&&(u.delete(v.id),or(p,re).catch(()=>{}));continue}let K=u.get(v.id);K?fp(p,K,{comment:`Move ${v.label} section (${v.tagName}) \u2014 from (${Math.round(k.x)},${Math.round(k.y)}) ${Math.round(k.width)}\xD7${Math.round(k.height)} to (${Math.round(D.x)},${Math.round(D.y)}) ${Math.round(D.width)}\xD7${Math.round(D.height)}`}).catch(re=>{console.warn("[Agentation] Failed to update rearrange annotation:",re)}):(u.set(v.id,""),xl(p,zt,{id:v.id,x:D.x/window.innerWidth*100,y:D.y,comment:`Move ${v.label} section (${v.tagName}) \u2014 from (${Math.round(k.x)},${Math.round(k.y)}) ${Math.round(k.width)}\xD7${Math.round(k.height)} to (${Math.round(D.x)},${Math.round(D.y)}) ${Math.round(D.width)}\xD7${Math.round(D.height)}`,element:v.selector,elementPath:"[rearrange]",timestamp:Date.now(),url:x,intent:"change",severity:"important",kind:"rearrange",rearrange:{selector:v.selector,label:v.label,tagName:v.tagName,originalRect:k,currentRect:D}}).then(re=>{u.has(v.id)&&u.set(v.id,re.id)}).catch(re=>{console.warn("[Agentation] Failed to sync rearrange annotation:",re),u.delete(v.id)}))}for(let[v,k]of u)h.has(v)||(u.delete(v),k&&or(p,k).catch(()=>{}))},300),()=>{Nl.current&&clearTimeout(Nl.current)}},[Ce,p,zt,ge]);let Wr=(0,M.useRef)(new Map);(0,M.useLayoutEffect)(()=>{let u=Ce?.sections??[],h=new Set;if((se||Te)&&N)for(let x of u){h.add(x.id);try{let v=document.querySelector(x.selector);if(!v)continue;if(!Wr.current.has(x.id)){let k={transform:v.style.transform,transformOrigin:v.style.transformOrigin,opacity:v.style.opacity,position:v.style.position,zIndex:v.style.zIndex,display:v.style.display},D=[],X=v.parentElement;for(;X&&X!==document.body;){let re=getComputedStyle(X);(re.overflow!=="visible"||re.overflowX!=="visible"||re.overflowY!=="visible")&&(D.push({el:X,overflow:X.style.overflow}),X.style.overflow="visible"),X=X.parentElement}getComputedStyle(v).display==="inline"&&(v.style.display="inline-block"),Wr.current.set(x.id,{el:v,origStyles:k,ancestors:D}),v.style.transformOrigin="top left",v.style.zIndex="9999"}}catch{}}for(let[x,v]of Wr.current)if(!h.has(x)){let{el:k,origStyles:D,ancestors:X}=v;k.style.transition="transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.4s cubic-bezier(0.22, 1, 0.36, 1)",k.style.transform=D.transform,k.style.transformOrigin=D.transformOrigin,k.style.opacity=D.opacity,k.style.position=D.position,k.style.zIndex=D.zIndex,Wr.current.delete(x),fe(()=>{k.style.transition="",k.style.display=D.display;for(let K of X)K.el.style.overflow=K.overflow},450)}},[Ce,se,Te,N]),(0,M.useEffect)(()=>()=>{for(let[,u]of Wr.current){let{el:h,origStyles:x,ancestors:v}=u;h.style.transition="transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.4s cubic-bezier(0.22, 1, 0.36, 1)",h.style.transform=x.transform,h.style.transformOrigin=x.transformOrigin,h.style.opacity=x.opacity,h.style.position=x.position,h.style.zIndex=x.zIndex,fe(()=>{h.style.transition="",h.style.display=x.display;for(let k of v)k.el.style.overflow=k.overflow},450)}Wr.current.clear()},[]);let Qi=(0,M.useCallback)(()=>{Le(!0),nt(!1),Ie(null),clearTimeout(ji.current),ji.current=fe(()=>{Le(!1)},300)},[]),c_=(0,M.useCallback)(()=>{se&&(Le(!0),nt(!1),Ie(null),clearTimeout(ji.current),ji.current=fe(()=>{Le(!1)},300)),L(!1)},[se]),d_=(0,M.useCallback)(()=>{I||(Ny(),z(!0))},[I]),Vi=(0,M.useCallback)(()=>{I&&(Gh(),z(!1))},[I]),Xa=(0,M.useCallback)(()=>{I?Vi():d_()},[I,d_,Vi]),u_=(0,M.useCallback)(()=>{if(Tt.length===0)return;let u=Tt[0],h=u.element,x=Tt.length>1,v=Tt.map(k=>k.element.getBoundingClientRect());if(x){let k={left:Math.min(...v.map(te=>te.left)),top:Math.min(...v.map(te=>te.top)),right:Math.max(...v.map(te=>te.right)),bottom:Math.max(...v.map(te=>te.bottom))},D=Tt.slice(0,5).map(te=>te.name).join(", "),X=Tt.length>5?` +${Tt.length-5} more`:"",K=v.map(te=>({x:te.left,y:te.top+window.scrollY,width:te.width,height:te.height})),ce=Tt[Tt.length-1].element,de=v[v.length-1],Me=de.left+de.width/2,Oe=de.top+de.height/2,_e=Eu(ce);me({x:Me/window.innerWidth*100,y:_e?Oe:Oe+window.scrollY,clientY:Oe,element:`${Tt.length} elements: ${D}${X}`,elementPath:"multi-select",boundingBox:{x:k.left,y:k.top+window.scrollY,width:k.right-k.left,height:k.bottom-k.top},isMultiSelect:!0,isFixed:_e,elementBoundingBoxes:K,multiSelectElements:Tt.map(te=>te.element),targetElement:ce,fullPath:Ma(h),accessibility:Sa(h),computedStyles:Ca(h),computedStylesObj:ka(h),nearbyElements:ba(h),cssClasses:bl(h),nearbyText:wl(h),sourceFile:Ra(h)})}else{let k=v[0],D=Eu(h);me({x:k.left/window.innerWidth*100,y:D?k.top:k.top+window.scrollY,clientY:k.top,element:u.name,elementPath:u.path,boundingBox:{x:k.left,y:D?k.top:k.top+window.scrollY,width:k.width,height:k.height},isFixed:D,fullPath:Ma(h),accessibility:Sa(h),computedStyles:Ca(h),computedStylesObj:ka(h),nearbyElements:ba(h),cssClasses:bl(h),nearbyText:wl(h),reactComponents:u.reactComponents,sourceFile:Ra(h)})}Br([]),We(null)},[Tt]);(0,M.useEffect)(()=>{N||(me(null),Y(null),xe(null),ve([]),We(null),J(!1),Br([]),oo.current={cmd:!1,shift:!1},I&&Vi())},[N,I,Vi]),(0,M.useEffect)(()=>()=>{Gh()},[]),(0,M.useEffect)(()=>{if(!N)return;let u=["p","span","h1","h2","h3","h4","h5","h6","li","td","th","label","blockquote","figcaption","caption","legend","dt","dd","pre","code","em","strong","b","i","u","s","a","time","address","cite","q","abbr","dfn","mark","small","sub","sup","[contenteditable]"].join(", "),h=":not([data-agentation-root]):not([data-agentation-root] *)",x=document.createElement("style");return x.id="feedback-cursor-styles",x.textContent=`
      body ${h} {
        cursor: crosshair !important;
      }

      body :is(${u})${h} {
        cursor: text !important;
      }
    `,document.head.appendChild(x),()=>{let v=document.getElementById("feedback-cursor-styles");v&&v.remove()}},[N]),(0,M.useEffect)(()=>{if(Yu!==null&&N)return document.documentElement.setAttribute("data-drawing-hover",""),()=>document.documentElement.removeAttribute("data-drawing-hover")},[Yu,N]),(0,M.useEffect)(()=>{if(!N||Q||jn||se)return;let u=h=>{let x=h.composedPath()[0]||h.target;if(en(x,"[data-feedback-toolbar]")){We(null);return}let v=Lr(h.clientX,h.clientY);if(!v||en(v,"[data-feedback-toolbar]")){We(null);return}let{name:k,elementName:D,path:X,reactComponents:K}=Su(v,ir),re=v.getBoundingClientRect();We({element:k,elementName:D,elementPath:X,rect:re,reactComponents:K}),qe({x:h.clientX,y:h.clientY})};return document.addEventListener("mousemove",u),()=>document.removeEventListener("mousemove",u)},[N,Q,jn,se,ir,Ln]);let Ki=(0,M.useCallback)(u=>{if(Y(u),Po(null),gn(null),dn([]),u.elementBoundingBoxes?.length){let h=[];for(let x of u.elementBoundingBoxes){let v=x.x+x.width/2,k=x.y+x.height/2-window.scrollY,D=Lr(v,k);D&&h.push(D)}ve(h),xe(null)}else if(u.boundingBox){let h=u.boundingBox,x=h.x+h.width/2,v=u.isFixed?h.y+h.height/2:h.y+h.height/2-window.scrollY,k=Lr(x,v);if(k){let D=k.getBoundingClientRect(),X=D.width/h.width,K=D.height/h.height;X<.5||K<.5?xe(null):xe(k)}else xe(null);ve([])}else xe(null),ve([])},[]);(0,M.useEffect)(()=>{if(!N||jn||se)return;let u=h=>{if(Yi.current){Yi.current=!1;return}let x=h.composedPath()[0]||h.target;if(en(x,"[data-feedback-toolbar]")||en(x,"[data-annotation-popup]")||en(x,"[data-annotation-marker]"))return;if(h.metaKey&&h.shiftKey&&!Q&&!Pe){h.preventDefault(),h.stopPropagation();let at=Lr(h.clientX,h.clientY);if(!at)return;let Ot=at.getBoundingClientRect(),{name:rt,path:$t,reactComponents:be}=Su(at,ir),Ne=Tt.findIndex(vt=>vt.element===at);Ne>=0?Br(vt=>vt.filter((Et,Un)=>Un!==Ne)):Br(vt=>[...vt,{element:at,rect:Ot,name:rt,path:$t,reactComponents:be??void 0}]);return}let v=en(x,"button, a, input, select, textarea, [role='button'], [onclick]");if(De.blockInteractions&&v&&(h.preventDefault(),h.stopPropagation()),Q){if(v&&!De.blockInteractions)return;h.preventDefault(),i_.current?.shake();return}if(Pe){if(v&&!De.blockInteractions)return;h.preventDefault(),s_.current?.shake();return}h.preventDefault();let k=Lr(h.clientX,h.clientY);if(!k)return;let{name:D,path:X,reactComponents:K}=Su(k,ir),re=k.getBoundingClientRect(),ce=h.clientX/window.innerWidth*100,de=Eu(k),Me=de?h.clientY:h.clientY+window.scrollY,Oe=window.getSelection(),_e;Oe&&Oe.toString().trim().length>0&&(_e=Oe.toString().trim().slice(0,500));let te=ka(k),Nt=Ca(k);me({x:ce,y:Me,clientY:h.clientY,element:D,elementPath:X,selectedText:_e,boundingBox:{x:re.left,y:de?re.top:re.top+window.scrollY,width:re.width,height:re.height},nearbyText:wl(k),cssClasses:bl(k),isFixed:de,fullPath:Ma(k),accessibility:Sa(k),computedStyles:Nt,computedStylesObj:te,nearbyElements:ba(k),reactComponents:K??void 0,sourceFile:Ra(k),targetElement:k}),We(null)};return document.addEventListener("click",u,!0),()=>document.removeEventListener("click",u,!0)},[N,jn,se,Q,Pe,De.blockInteractions,ir,Tt]),(0,M.useEffect)(()=>{if(!N)return;let u=v=>{v.key==="Meta"&&(oo.current.cmd=!0),v.key==="Shift"&&(oo.current.shift=!0)},h=v=>{let k=oo.current.cmd&&oo.current.shift;v.key==="Meta"&&(oo.current.cmd=!1),v.key==="Shift"&&(oo.current.shift=!1);let D=oo.current.cmd&&oo.current.shift;k&&!D&&Tt.length>0&&u_()},x=()=>{oo.current={cmd:!1,shift:!1},Br([])};return document.addEventListener("keydown",u),document.addEventListener("keyup",h),window.addEventListener("blur",x),()=>{document.removeEventListener("keydown",u),document.removeEventListener("keyup",h),window.removeEventListener("blur",x)}},[N,Tt,u_]),(0,M.useEffect)(()=>{if(!N||Q||jn||se)return;let u=h=>{let x=h.composedPath()[0]||h.target;en(x,"[data-feedback-toolbar]")||en(x,"[data-annotation-marker]")||en(x,"[data-annotation-popup]")||new Set(["P","SPAN","H1","H2","H3","H4","H5","H6","LI","TD","TH","LABEL","BLOCKQUOTE","FIGCAPTION","CAPTION","LEGEND","DT","DD","PRE","CODE","EM","STRONG","B","I","U","S","A","TIME","ADDRESS","CITE","Q","ABBR","DFN","MARK","SMALL","SUB","SUP"]).has(x.tagName)||x.isContentEditable||(h.preventDefault(),Ar.current={x:h.clientX,y:h.clientY})};return document.addEventListener("mousedown",u),()=>document.removeEventListener("mousedown",u)},[N,Q,jn,se]),(0,M.useEffect)(()=>{if(!N||Q)return;let u=h=>{if(!Ar.current)return;let x=h.clientX-Ar.current.x,v=h.clientY-Ar.current.y,k=x*x+v*v,D=Ha*Ha;if(!xo&&k>=D&&(lo.current=Ar.current,o_(!0),h.preventDefault()),(xo||k>=D)&&lo.current){if(Pl.current){let be=Math.min(lo.current.x,h.clientX),Ne=Math.min(lo.current.y,h.clientY),vt=Math.abs(h.clientX-lo.current.x),Et=Math.abs(h.clientY-lo.current.y);Pl.current.style.transform=`translate(${be}px, ${Ne}px)`,Pl.current.style.width=`${vt}px`,Pl.current.style.height=`${Et}px`}let X=Date.now();if(X-r_.current<gm)return;r_.current=X;let K=lo.current.x,re=lo.current.y,ce=Math.min(K,h.clientX),de=Math.min(re,h.clientY),Me=Math.max(K,h.clientX),Oe=Math.max(re,h.clientY),_e=(ce+Me)/2,te=(de+Oe)/2,Nt=new Set,at=[[ce,de],[Me,de],[ce,Oe],[Me,Oe],[_e,te],[_e,de],[_e,Oe],[ce,te],[Me,te]];for(let[be,Ne]of at){let vt=document.elementsFromPoint(be,Ne);for(let Et of vt)Et instanceof HTMLElement&&Nt.add(Et)}let Ot=document.querySelectorAll("button, a, input, img, p, h1, h2, h3, h4, h5, h6, li, label, td, th, div, span, section, article, aside, nav");for(let be of Ot)if(be instanceof HTMLElement){let Ne=be.getBoundingClientRect(),vt=Ne.left+Ne.width/2,Et=Ne.top+Ne.height/2,Un=vt>=ce&&vt<=Me&&Et>=de&&Et<=Oe,In=Math.min(Ne.right,Me)-Math.max(Ne.left,ce),Ut=Math.min(Ne.bottom,Oe)-Math.max(Ne.top,de),zl=In>0&&Ut>0?In*Ut:0,dr=Ne.width*Ne.height,To=dr>0?zl/dr:0;(Un||To>.5)&&Nt.add(be)}let rt=[],$t=new Set(["BUTTON","A","INPUT","IMG","P","H1","H2","H3","H4","H5","H6","LI","LABEL","TD","TH","SECTION","ARTICLE","ASIDE","NAV"]);for(let be of Nt){if(en(be,"[data-feedback-toolbar]")||en(be,"[data-annotation-marker]"))continue;let Ne=be.getBoundingClientRect();if(!(Ne.width>window.innerWidth*.8&&Ne.height>window.innerHeight*.5)&&!(Ne.width<10||Ne.height<10)&&Ne.left<Me&&Ne.right>ce&&Ne.top<Oe&&Ne.bottom>de){let vt=be.tagName,Et=$t.has(vt);if(!Et&&(vt==="DIV"||vt==="SPAN")){let Un=be.textContent&&be.textContent.trim().length>0,In=be.onclick!==null||be.getAttribute("role")==="button"||be.getAttribute("role")==="link"||be.classList.contains("clickable")||be.hasAttribute("data-clickable");(Un||In)&&!be.querySelector("p, h1, h2, h3, h4, h5, h6, button, a")&&(Et=!0)}if(Et){let Un=!1;for(let In of rt)if(In.left<=Ne.left&&In.right>=Ne.right&&In.top<=Ne.top&&In.bottom>=Ne.bottom){Un=!0;break}Un||rt.push(Ne)}}}if(Tl.current){let be=Tl.current;for(;be.children.length>rt.length;)be.removeChild(be.lastChild);rt.forEach((Ne,vt)=>{let Et=be.children[vt];Et||(Et=document.createElement("div"),Et.className=W.selectedElementHighlight,be.appendChild(Et)),Et.style.transform=`translate(${Ne.left}px, ${Ne.top}px)`,Et.style.width=`${Ne.width}px`,Et.style.height=`${Ne.height}px`})}}};return document.addEventListener("mousemove",u,{passive:!0}),()=>document.removeEventListener("mousemove",u)},[N,Q,xo,Ha]),(0,M.useEffect)(()=>{if(!N)return;let u=h=>{let x=xo,v=lo.current;if(xo&&v){Yi.current=!0;let k=Math.min(v.x,h.clientX),D=Math.min(v.y,h.clientY),X=Math.max(v.x,h.clientX),K=Math.max(v.y,h.clientY),re=[];document.querySelectorAll("button, a, input, img, p, h1, h2, h3, h4, h5, h6, li, label, td, th").forEach(_e=>{if(!(_e instanceof HTMLElement)||en(_e,"[data-feedback-toolbar]")||en(_e,"[data-annotation-marker]"))return;let te=_e.getBoundingClientRect();te.width>window.innerWidth*.8&&te.height>window.innerHeight*.5||te.width<10||te.height<10||te.left<X&&te.right>k&&te.top<K&&te.bottom>D&&re.push({element:_e,rect:te})});let de=re.filter(({element:_e})=>!re.some(({element:te})=>te!==_e&&_e.contains(te))),Me=h.clientX/window.innerWidth*100,Oe=h.clientY+window.scrollY;if(de.length>0){let _e=de.reduce(($t,{rect:be})=>({left:Math.min($t.left,be.left),top:Math.min($t.top,be.top),right:Math.max($t.right,be.right),bottom:Math.max($t.bottom,be.bottom)}),{left:1/0,top:1/0,right:-1/0,bottom:-1/0}),te=de.slice(0,5).map(({element:$t})=>$r($t).name).join(", "),Nt=de.length>5?` +${de.length-5} more`:"",at=de[0].element,Ot=ka(at),rt=Ca(at);me({x:Me,y:Oe,clientY:h.clientY,element:`${de.length} elements: ${te}${Nt}`,elementPath:"multi-select",boundingBox:{x:_e.left,y:_e.top+window.scrollY,width:_e.right-_e.left,height:_e.bottom-_e.top},isMultiSelect:!0,fullPath:Ma(at),accessibility:Sa(at),computedStyles:rt,computedStylesObj:Ot,nearbyElements:ba(at),cssClasses:bl(at),nearbyText:wl(at),sourceFile:Ra(at)})}else{let _e=Math.abs(X-k),te=Math.abs(K-D);_e>20&&te>20&&me({x:Me,y:Oe,clientY:h.clientY,element:"Area selection",elementPath:`region at (${Math.round(k)}, ${Math.round(D)})`,boundingBox:{x:k,y:D+window.scrollY,width:_e,height:te},isMultiSelect:!0})}We(null)}else x&&(Yi.current=!0);Ar.current=null,lo.current=null,o_(!1),Tl.current&&(Tl.current.innerHTML="")};return document.addEventListener("mouseup",u),()=>document.removeEventListener("mouseup",u)},[N,xo]);let io=(0,M.useCallback)(async(u,h,x)=>{let v=De.webhookUrl||R;if(!v||!De.webhooksEnabled&&!x)return!1;try{return(await fetch(v,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({event:u,timestamp:Date.now(),url:typeof window<"u"?window.location.href:void 0,...h})})).ok}catch(k){return console.warn("[Agentation] Webhook failed:",k),!1}},[R,De.webhookUrl,De.webhooksEnabled]),xm=(0,M.useCallback)(u=>{if(!Q)return;let h={id:Date.now().toString(),x:Q.x,y:Q.y,comment:u,element:Q.element,elementPath:Q.elementPath,timestamp:Date.now(),selectedText:Q.selectedText,boundingBox:Q.boundingBox,nearbyText:Q.nearbyText,cssClasses:Q.cssClasses,isMultiSelect:Q.isMultiSelect,isFixed:Q.isFixed,fullPath:Q.fullPath,accessibility:Q.accessibility,computedStyles:Q.computedStyles,nearbyElements:Q.nearbyElements,reactComponents:Q.reactComponents,sourceFile:Q.sourceFile,elementBoundingBoxes:Q.elementBoundingBoxes,...p&&zt?{sessionId:zt,url:typeof window<"u"?window.location.href:void 0,status:"pending"}:{}};g(x=>[...x,h]),Xi.current=h.id,fe(()=>{Xi.current=null},300),fe(()=>{$l(x=>new Set(x).add(h.id))},250),o?.(h),io("annotation.add",{annotation:h}),Ui(!0),fe(()=>{me(null),Ui(!1)},150),window.getSelection()?.removeAllRanges(),p&&zt&&xl(p,zt,h).then(x=>{x.id!==h.id&&(g(v=>v.map(k=>k.id===h.id?{...k,id:x.id}:k)),$l(v=>{let k=new Set(v);return k.delete(h.id),k.add(x.id),k}))}).catch(x=>{console.warn("[Agentation] Failed to sync annotation:",x)})},[Q,o,io,p,zt]),Qa=(0,M.useCallback)(()=>{Ui(!0),fe(()=>{me(null),Ui(!1)},150)},[]),Va=(0,M.useCallback)(u=>{let h=f.findIndex(v=>v.id===u),x=f[h];Pe?.id===u&&(Or(!0),fe(()=>{Y(null),xe(null),ve([]),Or(!1)},150)),to(u),Hi(v=>new Set(v).add(u)),x&&(r?.(x),io("annotation.delete",{annotation:x})),p&&or(p,u).catch(v=>{console.warn("[Agentation] Failed to delete annotation from server:",v)}),fe(()=>{g(v=>v.filter(k=>k.id!==u)),Hi(v=>{let k=new Set(v);return k.delete(u),k}),to(null),h<f.length-1&&(Wn(h),fe(()=>Wn(null),200))},150)},[f,Pe,r,io,p]),qi=(0,M.useCallback)(u=>{if(!u){Po(null),gn(null),dn([]);return}if(Po(u.id),u.elementBoundingBoxes?.length){let h=[];for(let x of u.elementBoundingBoxes){let v=x.x+x.width/2,k=x.y+x.height/2-window.scrollY,X=document.elementsFromPoint(v,k).find(K=>!K.closest("[data-annotation-marker]")&&!K.closest("[data-agentation-root]"));X&&h.push(X)}dn(h),gn(null)}else if(u.boundingBox){let h=u.boundingBox,x=h.x+h.width/2,v=u.isFixed?h.y+h.height/2:h.y+h.height/2-window.scrollY,k=Lr(x,v);if(k){let D=k.getBoundingClientRect(),X=D.width/h.width,K=D.height/h.height;X<.5||K<.5?gn(null):gn(k)}else gn(null);dn([])}else gn(null),dn([])},[]),vm=(0,M.useCallback)(u=>{if(!Pe)return;let h={...Pe,comment:u};g(x=>x.map(v=>v.id===Pe.id?h:v)),l?.(h),io("annotation.update",{annotation:h}),p&&fp(p,Pe.id,{comment:u}).catch(x=>{console.warn("[Agentation] Failed to update annotation on server:",x)}),Or(!0),fe(()=>{Y(null),xe(null),ve([]),Or(!1)},150)},[Pe,l,io,p]),wm=(0,M.useCallback)(()=>{Or(!0),fe(()=>{Y(null),xe(null),ve([]),Or(!1)},150)},[]),cr=(0,M.useCallback)(()=>{let u=f.length,h=ae.length>0||!!Ce;if(u===0&&Ln.length===0&&!h)return;if(i?.(f),io("annotations.clear",{annotations:f}),p){Promise.all(f.map(k=>or(p,k.id).catch(D=>{console.warn("[Agentation] Failed to delete annotation from server:",D)})));for(let[,k]of Ll.current)k&&or(p,k).catch(()=>{});Ll.current.clear();for(let[,k]of Il.current)k&&or(p,k).catch(()=>{});Il.current.clear()}On(!0),Sn(!0),cm([]);let x=Aa.current;if(x){let k=x.getContext("2d");k&&k.clearRect(0,0,x.width,x.height)}(ae.length>0||Ce)&&(za(k=>k+1),Hu(k=>k+1),fe(()=>{ot([]),En(null)},200)),we&&ut(!1),It&&yo(""),lr.current={rearrange:null,placements:[]},Ia(ge);let v=u*30+200;fe(()=>{g([]),$l(new Set),localStorage.removeItem(Bi(ge)),On(!1)},v),fe(()=>Sn(!1),1500)},[ge,f,Ln,ae,Ce,we,It,i,io,p]),Ka=(0,M.useCallback)(async()=>{let u=typeof window<"u"?window.location.pathname+window.location.search+window.location.hash:ge,h=se&&we,x;if(h){if(ae.length===0&&!Ce&&!It)return;x=""}else{if(x=mp(f,u,De.outputDetail),!x&&Ln.length===0&&ae.length===0&&!Ce)return;x||(x=`## Page Feedback: ${u}
`)}if(!h&&Ln.length>0){let v=new Set;for(let K of f)K.drawingIndex!=null&&v.add(K.drawingIndex);let k=Aa.current;k&&(k.style.visibility="hidden");let D=[],X=window.scrollY;for(let K=0;K<Ln.length;K++){if(v.has(K))continue;let re=Ln[K];if(re.points.length<2)continue;let ce=re.fixed?re.points:re.points.map(Dt=>({x:Dt.x,y:Dt.y-X})),de=1/0,Me=1/0,Oe=-1/0,_e=-1/0;for(let Dt of ce)de=Math.min(de,Dt.x),Me=Math.min(Me,Dt.y),Oe=Math.max(Oe,Dt.x),_e=Math.max(_e,Dt.y);let te=Oe-de,Nt=_e-Me,at=Math.hypot(te,Nt),Ot=ce[0],rt=ce[ce.length-1],$t=Math.hypot(rt.x-Ot.x,rt.y-Ot.y),be,Ne=$t<at*.35,vt=te/Math.max(Nt,1);if(Ne&&at>20){let Dt=Math.max(te,Nt)*.15,Do=0;for(let ur of ce){let Cm=ur.x-de<Dt,Sm=Oe-ur.x<Dt,Mm=ur.y-Me<Dt,Em=_e-ur.y<Dt;(Cm||Sm)&&(Mm||Em)&&Do++}be=Do>ce.length*.15?"box":"circle"}else vt>3&&Nt<40?be="underline":$t>at*.5?be="arrow":be="drawing";let Et=Math.min(10,ce.length),Un=Math.max(1,Math.floor(ce.length/Et)),In=new Set,Ut=[],zl=[Ot];for(let Dt=Un;Dt<ce.length-1;Dt+=Un)zl.push(ce[Dt]);zl.push(rt);for(let Dt of zl){let Do=Lr(Dt.x,Dt.y);if(!Do||In.has(Do)||en(Do,"[data-feedback-toolbar]"))continue;In.add(Do);let{name:ur}=$r(Do);Ut.includes(ur)||Ut.push(ur)}let dr=`${Math.round(de)},${Math.round(Me)} \u2192 ${Math.round(Oe)},${Math.round(_e)}`,To;(be==="circle"||be==="box")&&Ut.length>0?To=`${be==="box"?"Boxed":"Circled"} **${Ut[0]}**${Ut.length>1?` (and ${Ut.slice(1).join(", ")})`:""} (region: ${dr})`:be==="underline"&&Ut.length>0?To=`Underlined **${Ut[0]}** (${dr})`:be==="arrow"&&Ut.length>=2?To=`Arrow from **${Ut[0]}** to **${Ut[Ut.length-1]}** (${Math.round(Ot.x)},${Math.round(Ot.y)} \u2192 ${Math.round(rt.x)},${Math.round(rt.y)})`:Ut.length>0?To=`${be==="arrow"?"Arrow":"Drawing"} near **${Ut.join("**, **")}** (region: ${dr})`:To=`Drawing at ${dr}`,D.push(To)}k&&(k.style.visibility=""),D.length>0&&(x+=`
**Drawings:**
`,D.forEach((K,re)=>{x+=`${re+1}. ${K}
`}))}if((ae.length>0||h&&It)&&(x+=`
`+cp(ae,{width:window.innerWidth,height:window.innerHeight},{blankCanvas:we,wireframePurpose:It||void 0},De.outputDetail)),Ce){let v=dp(Ce,De.outputDetail,{width:window.innerWidth,height:window.innerHeight});v&&(x+=`
`+v)}if(m)try{await navigator.clipboard.writeText(x)}catch{}s?.(x),Mt(!0),fe(()=>Mt(!1),2e3),De.autoClearAfterCopy&&fe(()=>cr(),500)},[f,Ln,ae,Ce,we,se,go,It,ge,De.outputDetail,ir,De.autoClearAfterCopy,cr,m,s]),qa=(0,M.useCallback)(async()=>{let u=typeof window<"u"?window.location.pathname+window.location.search+window.location.hash:ge,h=mp(f,u,De.outputDetail);if(!h&&ae.length===0&&!Ce)return;if(h||(h=`## Page Feedback: ${u}
`),ae.length>0&&(h+=`
`+cp(ae,{width:window.innerWidth,height:window.innerHeight},{blankCanvas:we,wireframePurpose:It||void 0},De.outputDetail)),Ce){let v=dp(Ce,De.outputDetail,{width:window.innerWidth,height:window.innerHeight});v&&(h+=`
`+v)}a&&a(h,f),tn("sending"),await new Promise(v=>fe(v,150));let x=await io("submit",{output:h,annotations:f},!0);tn(x?"sent":"failed"),fe(()=>tn("idle"),2500),x&&De.autoClearAfterCopy&&fe(()=>cr(),500)},[a,io,f,ae,Ce,we,go,ge,De.outputDetail,ir,De.autoClearAfterCopy,cr]);(0,M.useEffect)(()=>{if(!zr)return;let u=10,h=v=>{let k=v.clientX-zr.x,D=v.clientY-zr.y,X=Math.sqrt(k*k+D*D);if(!ar&&X>u&&Ju(!0),ar||X>u){let K=zr.toolbarX+k,re=zr.toolbarY+D,ce=20,de=337,Me=44,_e=de-(N?Hn==="connected"?297:257:44),te=ce-_e,Nt=window.innerWidth-ce-de;K=Math.max(te,Math.min(Nt,K)),re=Math.max(ce,Math.min(window.innerHeight-Me-ce,re)),Fa({x:K,y:re})}},x=()=>{ar&&(ja.current=!0),Ju(!1),e_(null)};return document.addEventListener("mousemove",h),document.addEventListener("mouseup",x),()=>{document.removeEventListener("mousemove",h),document.removeEventListener("mouseup",x)}},[zr,ar,N,Hn]);let bm=(0,M.useCallback)(u=>{if(u.target.closest("button")||u.target.closest("[data-agentation-settings-panel]"))return;let h=u.currentTarget.parentElement;if(!h)return;let x=h.getBoundingClientRect(),v=xt?.x??x.left,k=xt?.y??x.top;e_({x:u.clientX,y:u.clientY,toolbarX:v,toolbarY:k})},[xt]);if((0,M.useEffect)(()=>{if(!xt)return;let u=()=>{let k=xt.x,D=xt.y,re=20-(337-(N?Hn==="connected"?297:257:44)),ce=window.innerWidth-20-337;k=Math.max(re,Math.min(ce,k)),D=Math.max(20,Math.min(window.innerHeight-44-20,D)),(k!==xt.x||D!==xt.y)&&Fa({x:k,y:D})};return u(),window.addEventListener("resize",u),()=>window.removeEventListener("resize",u)},[xt,N,Hn]),(0,M.useEffect)(()=>{let u=h=>{let x=h.target,v=x.tagName==="INPUT"||x.tagName==="TEXTAREA"||x.isContentEditable;if(h.key==="Escape"){if(se){je?Ie(null):Qi();return}if(jn){Oa(!1);return}if(Tt.length>0){Br([]);return}Q||N&&(Vt(),L(!1))}if((h.metaKey||h.ctrlKey)&&h.shiftKey&&(h.key==="f"||h.key==="F")){h.preventDefault(),Vt(),N?c_():L(!0);return}if(!(v||h.metaKey||h.ctrlKey)&&((h.key==="p"||h.key==="P")&&(h.preventDefault(),Vt(),Xa()),(h.key==="l"||h.key==="L")&&(h.preventDefault(),Vt(),jn&&Oa(!1),A&&J(!1),Q&&Qa(),se?Qi():nt(!0)),(h.key==="h"||h.key==="H")&&f.length>0&&(h.preventDefault(),Vt(),$(k=>!k)),(h.key==="c"||h.key==="C")&&(f.length>0||ae.length>0||Ce)&&(h.preventDefault(),Vt(),Ka()),(h.key==="x"||h.key==="X")&&(f.length>0||ae.length>0||Ce)&&(h.preventDefault(),Vt(),cr(),ae.length>0&&ot([]),Ce&&En(null)),h.key==="s"||h.key==="S")){let k=ho(De.webhookUrl)||ho(R||"");f.length>0&&k&&cn==="idle"&&(h.preventDefault(),Vt(),qa())}};return document.addEventListener("keydown",u),()=>document.removeEventListener("keydown",u)},[N,jn,se,je,ae,Ce,Q,f.length,De.webhookUrl,R,cn,qa,Xa,Ka,cr,Tt]),!pe||U)return null;let Bl=f.length>0,Fr=f.filter(u=>!n_.has(u.id)&&u.kind!=="placement"&&u.kind!=="rearrange"),km=Fr.length>0,__=f.filter(u=>n_.has(u.id)),f_=u=>{let D=u.x/100*window.innerWidth,X=typeof u.y=="string"?parseFloat(u.y):u.y,K={};window.innerHeight-X-22-10<80&&(K.top="auto",K.bottom="calc(100% + 10px)");let ce=D-200/2,de=10;if(ce<de){let Me=de-ce;K.left=`calc(50% + ${Me}px)`}else if(ce+200>window.innerWidth-de){let Me=ce+200-(window.innerWidth-de);K.left=`calc(50% - ${Me}px)`}return K};return(0,bp.createPortal)((0,F.jsxs)("div",{ref:ye,style:{display:"contents"},"data-agentation-theme":ro?"dark":"light","data-agentation-accent":De.annotationColorId,"data-agentation-root":"",children:[(0,F.jsx)("div",{className:`${W.toolbar}${C?` ${C}`:""}`,"data-feedback-toolbar":!0,"data-agentation-toolbar":!0,style:xt?{left:xt.x,top:xt.y,right:"auto",bottom:"auto"}:void 0,children:(0,F.jsxs)("div",{className:`${W.toolbarContainer} ${N?W.expanded:W.collapsed} ${Ku?W.entrance:""} ${B?W.hiding:""} ${!De.webhooksEnabled&&(ho(De.webhookUrl)||ho(R||""))?W.serverConnected:""}`,onClick:N?void 0:u=>{if(ja.current){ja.current=!1,u.preventDefault();return}L(!0)},onMouseDown:bm,role:N?void 0:"button",tabIndex:N?-1:0,title:N?void 0:"Start feedback mode",children:[(0,F.jsxs)("div",{className:`${W.toggleContent} ${N?W.hidden:W.visible}`,children:[(0,F.jsx)(Cp,{size:24}),km&&(0,F.jsx)("span",{className:`${W.badge} ${N?W.fadeOut:""} ${Ku?W.entrance:""}`,children:Fr.length})]}),(0,F.jsxs)("div",{className:`${W.controlsContent} ${N?W.visible:W.hidden} ${xt&&xt.y<100?W.tooltipBelow:""} ${Fe||A?W.tooltipsHidden:""} ${Xu?W.tooltipsInSession:""}`,onMouseEnter:_m,onMouseLeave:fm,children:[(0,F.jsxs)("div",{className:`${W.buttonWrapper} ${xt&&xt.x<120?W.buttonWrapperAlignLeft:""}`,children:[(0,F.jsx)("button",{className:W.controlButton,onClick:u=>{u.stopPropagation(),Vt(),Xa()},"data-active":I,children:(0,F.jsx)(Ip,{size:24,isPaused:I})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:[I?"Resume animations":"Pause animations",(0,F.jsx)("span",{className:W.shortcut,children:"P"})]})]}),(0,F.jsxs)("div",{className:W.buttonWrapper,children:[(0,F.jsx)("button",{className:`${W.controlButton} ${ro?"":W.light}`,onClick:u=>{u.stopPropagation(),Vt(),jn&&Oa(!1),A&&J(!1),Q&&Qa(),se?Qi():nt(!0)},"data-active":se,style:se&&we?{color:"#f97316",background:"rgba(249, 115, 22, 0.25)"}:void 0,children:(0,F.jsx)(Op,{size:21})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:[se?"Exit layout mode":"Layout mode",(0,F.jsx)("span",{className:W.shortcut,children:"L"})]})]}),(0,F.jsxs)("div",{className:W.buttonWrapper,children:[(0,F.jsx)("button",{className:W.controlButton,onClick:u=>{u.stopPropagation(),Vt(),$(!w)},disabled:!Bl||se,children:(0,F.jsx)(Lp,{size:24,isOpen:w})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:[w?"Hide markers":"Show markers",(0,F.jsx)("span",{className:W.shortcut,children:"H"})]})]}),(0,F.jsxs)("div",{className:W.buttonWrapper,children:[(0,F.jsx)("button",{className:`${W.controlButton} ${Ye?W.statusShowing:""}`,onClick:u=>{u.stopPropagation(),Vt(),Ka()},disabled:se&&we?ae.length===0&&!Ce?.sections?.length:!Bl&&Ln.length===0&&ae.length===0&&!Ce?.sections?.length,"data-active":Ye,children:(0,F.jsx)(Mp,{size:24,copied:Ye,tint:se&&we&&(ae.length>0||Ce?.sections?.length)?"#f97316":void 0})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:[se&&we?"Copy layout":"Copy feedback",(0,F.jsx)("span",{className:W.shortcut,children:"C"})]})]}),(0,F.jsxs)("div",{className:`${W.buttonWrapper} ${W.sendButtonWrapper} ${N&&!De.webhooksEnabled&&(ho(De.webhookUrl)||ho(R||""))?W.sendButtonVisible:""}`,children:[(0,F.jsxs)("button",{className:`${W.controlButton} ${cn==="sent"||cn==="failed"?W.statusShowing:""}`,onClick:u=>{u.stopPropagation(),Vt(),qa()},disabled:!Bl||!ho(De.webhookUrl)&&!ho(R||"")||cn==="sending","data-no-hover":cn==="sent"||cn==="failed",tabIndex:ho(De.webhookUrl)||ho(R||"")?0:-1,children:[(0,F.jsx)(Ep,{size:24,state:cn}),Bl&&cn==="idle"&&(0,F.jsx)("span",{className:W.buttonBadge,children:f.length})]}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:["Send Annotations",(0,F.jsx)("span",{className:W.shortcut,children:"S"})]})]}),(0,F.jsxs)("div",{className:W.buttonWrapper,children:[(0,F.jsx)("button",{className:W.controlButton,onClick:u=>{u.stopPropagation(),Vt(),cr()},disabled:!Bl&&Ln.length===0&&ae.length===0&&!Ce?.sections?.length,"data-danger":!0,children:(0,F.jsx)($p,{size:24})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:["Clear all",(0,F.jsx)("span",{className:W.shortcut,children:"X"})]})]}),(0,F.jsxs)("div",{className:W.buttonWrapper,children:[(0,F.jsx)("button",{className:W.controlButton,onClick:u=>{u.stopPropagation(),Vt(),se&&Qi(),J(!A)},children:(0,F.jsx)(Np,{size:24})}),p&&Hn!=="disconnected"&&(0,F.jsx)("span",{className:`${W.mcpIndicator} ${W[Hn]} ${A?W.hidden:""}`,title:Hn==="connected"?"MCP Connected":"MCP Connecting..."}),(0,F.jsx)("span",{className:W.buttonTooltip,children:"Settings"})]}),(0,F.jsx)("div",{className:W.divider}),(0,F.jsxs)("div",{className:`${W.buttonWrapper} ${xt&&typeof window<"u"&&xt.x>window.innerWidth-120?W.buttonWrapperAlignRight:""}`,children:[(0,F.jsx)("button",{className:W.controlButton,onClick:u=>{u.stopPropagation(),Vt(),c_()},children:(0,F.jsx)(Rp,{size:24})}),(0,F.jsxs)("span",{className:W.buttonTooltip,children:["Exit",(0,F.jsx)("span",{className:W.shortcut,children:"Esc"})]})]})]}),(0,F.jsx)(t2,{visible:se&&N,activeType:je,onSelect:u=>{Ie(je===u?null:u)},isDarkMode:ro,sectionCount:Ce?.sections.length??0,onDetectSections:()=>{let u=h2(),h=Ce?.sections??[],x=new Set(h.map(X=>X.selector)),v=u.filter(X=>!x.has(X.selector)),k=[...h,...v],D=[...Ce?.originalOrder??[],...v.map(X=>X.id)];En({sections:k,originalOrder:D,detectedAt:Date.now()})},placementCount:ae.length,onClearPlacements:()=>{za(u=>u+1),Hu(u=>u+1),fe(()=>{En({sections:[],originalOrder:[],detectedAt:Date.now()})},200)},blankCanvas:we,onBlankCanvasChange:u=>{let h={sections:[],originalOrder:[],detectedAt:Date.now()};u?(Ba.current={rearrange:Ce,placements:ae},En(lr.current.rearrange||h),ot(lr.current.placements),Ie(null)):(lr.current={rearrange:Ce,placements:ae},En(Ba.current.rearrange||h),ot(Ba.current.placements)),ut(u)},wireframePurpose:It,onWireframePurposeChange:yo,Tooltip:Nr,onDragStart:(u,h)=>{h.preventDefault();let x=ee[u],v=null,k=!1,D=h.clientX,X=h.clientY,re=h.target.closest("[data-feedback-toolbar]")?.getBoundingClientRect().top??window.innerHeight,ce=Me=>{let Oe=Me.clientX-D,_e=Me.clientY-X;if(!k&&(Math.abs(Oe)>4||Math.abs(_e)>4)&&(k=!0,v=document.createElement("div"),v.className=`${T.dragPreview}${we?` ${T.dragPreviewWireframe}`:""}`,document.body.appendChild(v)),!v)return;let te=Math.max(0,re-Me.clientY),Nt=Math.min(1,te/180),at=1-Math.pow(1-Nt,2),Ot=28,rt=20,$t=Math.min(140,x.width*.18),be=Math.min(90,x.height*.18),Ne=Ot+($t-Ot)*at,vt=rt+(be-rt)*at;v.style.width=`${Ne}px`,v.style.height=`${vt}px`,v.style.left=`${Me.clientX-Ne/2}px`,v.style.top=`${Me.clientY-vt/2}px`,v.style.opacity=`${.5+.5*at}`,v.textContent=at>.25?u:""},de=Me=>{if(window.removeEventListener("mousemove",ce),window.removeEventListener("mouseup",de),v&&document.body.removeChild(v),k){let Oe=x.width,_e=x.height,te=window.scrollY,Nt=Math.max(0,Me.clientX-Oe/2),at=Math.max(0,Me.clientY+te-_e/2),Ot={id:`dp-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,type:u,x:Nt,y:at,width:Oe,height:_e,scrollY:te,timestamp:Date.now()};ot(rt=>[...rt,Ot]),Ie(null),El.current=new Set,ju(rt=>rt+1)}};window.addEventListener("mousemove",ce),window.addEventListener("mouseup",de)}}),(0,F.jsx)(kx,{settings:De,onSettingsChange:u=>hm(h=>({...h,...u})),isDarkMode:ro,onToggleTheme:pm,isDevMode:Gu,connectionStatus:Hn,endpoint:p,isVisible:le,toolbarNearBottom:!!xt&&xt.y<230,settingsPage:ie,onSettingsPageChange:Se,onHideToolbar:ym})]})}),(se||Te)&&(0,F.jsx)("div",{className:`${T.blankCanvas} ${Ft?T.visible:""} ${Wi?T.gridActive:""}`,style:{"--canvas-opacity":no},"data-feedback-toolbar":!0}),se&&we&&Ft&&(0,F.jsxs)("div",{className:T.wireframeNotice,"data-feedback-toolbar":!0,children:[(0,F.jsxs)("div",{className:T.wireframeOpacityRow,children:[(0,F.jsx)("span",{className:T.wireframeOpacityLabel,children:"Toggle Opacity"}),(0,F.jsx)("input",{type:"range",className:T.wireframeOpacitySlider,min:0,max:1,step:.01,value:no,onChange:u=>un(Number(u.target.value))})]}),(0,F.jsxs)("div",{className:T.wireframeNoticeTitleRow,children:[(0,F.jsx)("span",{className:T.wireframeNoticeTitle,children:"Wireframe Mode"}),(0,F.jsx)("span",{className:T.wireframeNoticeDivider}),(0,F.jsx)("button",{className:T.wireframeStartOver,onClick:()=>{za(u=>u+1),En({sections:[],originalOrder:[],detectedAt:Date.now()}),lr.current={rearrange:null,placements:[]},yo(""),Ia(ge)},children:"Start Over"})]}),"Drag components onto the canvas.",(0,F.jsx)("br",{}),"Copied output will only include the wireframed layout."]}),(se||Te)&&(0,F.jsx)(q5,{placements:ae,onChange:ot,activeComponent:Te?null:je,onActiveComponentChange:Ie,isDarkMode:ro,exiting:Te,onInteractionChange:om,passthrough:!je,extraSnapRects:Ce?.sections.map(u=>u.currentRect),deselectSignal:rm,clearSignal:sm,wireframe:we,onSelectionChange:(u,h)=>{El.current=u,h||(Fi.current=new Set,im(x=>x+1))},onDragMove:(u,h)=>{let x=Fi.current;if(!(!x.size||!Ce)){if(!Fn.current){Fn.current=new Map;for(let v of Ce.sections)x.has(v.id)&&Fn.current.set(v.id,{x:v.currentRect.x,y:v.currentRect.y})}for(let v of Ce.sections){if(!x.has(v.id)||!Fn.current.get(v.id))continue;let D=document.querySelector(`[data-rearrange-section="${v.id}"]`);D&&(D.style.transform=`translate(${u}px, ${h}px)`)}}},onDragEnd:(u,h,x)=>{let v=Fi.current,k=Fn.current;if(Fn.current=null,!(!v.size||!Ce||!k)){for(let D of v){let X=document.querySelector(`[data-rearrange-section="${D}"]`);X&&(X.style.transform="")}x&&En(D=>D&&{...D,sections:D.sections.map(X=>{let K=k.get(X.id);return K?{...X,currentRect:{...X.currentRect,x:Math.max(0,K.x+u),y:Math.max(0,K.y+h)}}:X})})}}}),(se||Te)&&Ce&&(0,F.jsx)(g2,{rearrangeState:Ce,onChange:En,isDarkMode:ro,exiting:Te,blankCanvas:we,extraSnapRects:ae.map(u=>({x:u.x,y:u.y,width:u.width,height:u.height})),clearSignal:am,deselectSignal:lm,onSelectionChange:(u,h)=>{Fi.current=u,h||(El.current=new Set,ju(x=>x+1))},onDragMove:(u,h)=>{let x=El.current;if(x.size){if(!Fn.current){Fn.current=new Map;for(let v of ae)x.has(v.id)&&Fn.current.set(v.id,{x:v.x,y:v.y})}for(let v of x){let k=document.querySelector(`[data-design-placement="${v}"]`);k&&(k.style.transform=`translate(${u}px, ${h}px)`)}}},onDragEnd:(u,h,x)=>{let v=El.current,k=Fn.current;if(Fn.current=null,!(!v.size||!k)){for(let D of v){let X=document.querySelector(`[data-design-placement="${D}"]`);X&&(X.style.transform="")}x&&ot(D=>D.map(X=>{let K=k.get(X.id);return K?{...X,x:Math.max(0,K.x+u),y:Math.max(0,K.y+h)}:X}))}}}),(0,F.jsx)("canvas",{ref:Aa,className:`${W.drawCanvas} ${jn?W.active:""}`,style:{opacity:Ua?1:0,transition:"opacity 0.15s ease"},"data-feedback-toolbar":!0}),(0,F.jsxs)("div",{className:W.markersLayer,"data-feedback-toolbar":!0,children:[Z&&Fr.filter(u=>!u.isFixed).map((u,h,x)=>(0,F.jsx)(gp,{annotation:u,globalIndex:Fr.findIndex(v=>v.id===u.id),layerIndex:h,layerSize:x.length,isExiting:Ge,isClearing:Ro,isAnimated:t_.has(u.id),isHovered:!Ge&&mo===u.id,isDeleting:eo===u.id,isEditingAny:!!Pe,renumberFrom:Tr,markerClickBehavior:De.markerClickBehavior,tooltipStyle:f_(u),onHoverEnter:v=>!Ge&&v.id!==Xi.current&&qi(v),onHoverLeave:()=>qi(null),onClick:v=>De.markerClickBehavior==="delete"?Va(v.id):Ki(v),onContextMenu:Ki},u.id)),Z&&!Ge&&__.filter(u=>!u.isFixed).map(u=>(0,F.jsx)(yp,{annotation:u},u.id))]}),(0,F.jsxs)("div",{className:W.fixedMarkersLayer,"data-feedback-toolbar":!0,children:[Z&&Fr.filter(u=>u.isFixed).map((u,h,x)=>(0,F.jsx)(gp,{annotation:u,globalIndex:Fr.findIndex(v=>v.id===u.id),layerIndex:h,layerSize:x.length,isExiting:Ge,isClearing:Ro,isAnimated:t_.has(u.id),isHovered:!Ge&&mo===u.id,isDeleting:eo===u.id,isEditingAny:!!Pe,renumberFrom:Tr,markerClickBehavior:De.markerClickBehavior,tooltipStyle:f_(u),onHoverEnter:v=>!Ge&&v.id!==Xi.current&&qi(v),onHoverLeave:()=>qi(null),onClick:v=>De.markerClickBehavior==="delete"?Va(v.id):Ki(v),onContextMenu:Ki},u.id)),Z&&!Ge&&__.filter(u=>u.isFixed).map(u=>(0,F.jsx)(yp,{annotation:u,fixed:!0},u.id))]}),N&&(0,F.jsxs)("div",{className:W.overlay,"data-feedback-toolbar":!0,style:Q||Pe?{zIndex:99999}:void 0,children:[Re?.rect&&!Q&&!Xe&&!xo&&(0,F.jsx)("div",{className:`${W.hoverHighlight} ${W.enter}`,style:{left:Re.rect.left,top:Re.rect.top,width:Re.rect.width,height:Re.rect.height,borderColor:"color-mix(in srgb, var(--agentation-color-accent) 50%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 4%, transparent)"}}),Tt.filter(u=>document.contains(u.element)).map((u,h)=>{let x=u.element.getBoundingClientRect(),v=Tt.length>1;return(0,F.jsx)("div",{className:v?W.multiSelectOutline:W.singleSelectOutline,style:{position:"fixed",left:x.left,top:x.top,width:x.width,height:x.height,...v?{}:{borderColor:"color-mix(in srgb, var(--agentation-color-accent) 60%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 5%, transparent)"}}},h)}),mo&&!Q&&(()=>{let u=f.find(k=>k.id===mo);if(!u?.boundingBox)return null;if(u.elementBoundingBoxes?.length)return An.length>0?An.filter(k=>document.contains(k)).map((k,D)=>{let X=k.getBoundingClientRect();return(0,F.jsx)("div",{className:`${W.multiSelectOutline} ${W.enter}`,style:{left:X.left,top:X.top,width:X.width,height:X.height}},`hover-outline-live-${D}`)}):u.elementBoundingBoxes.map((k,D)=>(0,F.jsx)("div",{className:`${W.multiSelectOutline} ${W.enter}`,style:{left:k.x,top:k.y-Ze,width:k.width,height:k.height}},`hover-outline-${D}`));let h=rr&&document.contains(rr)?rr.getBoundingClientRect():null,x=h?{x:h.left,y:h.top,width:h.width,height:h.height}:{x:u.boundingBox.x,y:u.isFixed?u.boundingBox.y:u.boundingBox.y-Ze,width:u.boundingBox.width,height:u.boundingBox.height},v=u.isMultiSelect;return(0,F.jsx)("div",{className:`${v?W.multiSelectOutline:W.singleSelectOutline} ${W.enter}`,style:{left:x.x,top:x.y,width:x.width,height:x.height,...v?{}:{borderColor:"color-mix(in srgb, var(--agentation-color-accent) 60%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 5%, transparent)"}}})})(),Re&&!Q&&!Xe&&!xo&&(0,F.jsxs)("div",{className:`${W.hoverTooltip} ${W.enter}`,style:{left:Math.max(8,Math.min(Ee.x,window.innerWidth-100)),top:Math.max(Ee.y-(Re.reactComponents?48:32),8)},children:[Re.reactComponents&&(0,F.jsx)("div",{className:W.hoverReactPath,children:Re.reactComponents}),(0,F.jsx)("div",{className:W.hoverElementName,children:Re.elementName})]}),Q&&(0,F.jsxs)(F.Fragment,{children:[Q.multiSelectElements?.length?Q.multiSelectElements.filter(u=>document.contains(u)).map((u,h)=>{let x=u.getBoundingClientRect();return(0,F.jsx)("div",{className:`${W.multiSelectOutline} ${Rl?W.exit:W.enter}`,style:{left:x.left,top:x.top,width:x.width,height:x.height}},`pending-multi-${h}`)}):Q.targetElement&&document.contains(Q.targetElement)?(()=>{let u=Q.targetElement.getBoundingClientRect();return(0,F.jsx)("div",{className:`${W.singleSelectOutline} ${Rl?W.exit:W.enter}`,style:{left:u.left,top:u.top,width:u.width,height:u.height,borderColor:"color-mix(in srgb, var(--agentation-color-accent) 60%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 5%, transparent)"}})})():Q.boundingBox&&(0,F.jsx)("div",{className:`${Q.isMultiSelect?W.multiSelectOutline:W.singleSelectOutline} ${Rl?W.exit:W.enter}`,style:{left:Q.boundingBox.x,top:Q.boundingBox.y-Ze,width:Q.boundingBox.width,height:Q.boundingBox.height,...Q.isMultiSelect?{}:{borderColor:"color-mix(in srgb, var(--agentation-color-accent) 60%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 5%, transparent)"}}}),(()=>{let u=Q.x,h=Q.isFixed?Q.y:Q.y-Ze;return(0,F.jsxs)(F.Fragment,{children:[(0,F.jsx)(fx,{x:u,y:h,isMultiSelect:Q.isMultiSelect,isExiting:Rl}),(0,F.jsx)(Di,{ref:i_,element:Q.element,selectedText:Q.selectedText,computedStyles:Q.computedStylesObj,placeholder:Q.element==="Area selection"?"What should change in this area?":Q.isMultiSelect?"Feedback for this group of elements...":"What should change?",onSubmit:xm,onCancel:Qa,isExiting:Rl,lightMode:!ro,accentColor:Q.isMultiSelect?"var(--agentation-color-green)":"var(--agentation-color-accent)",style:{left:Math.max(160,Math.min(window.innerWidth-160,u/100*window.innerWidth)),...h>window.innerHeight-290?{bottom:window.innerHeight-h+20}:{top:h+20}}})]})})()]}),Pe&&(0,F.jsxs)(F.Fragment,{children:[Pe.elementBoundingBoxes?.length?$e.length>0?$e.filter(u=>document.contains(u)).map((u,h)=>{let x=u.getBoundingClientRect();return(0,F.jsx)("div",{className:`${W.multiSelectOutline} ${W.enter}`,style:{left:x.left,top:x.top,width:x.width,height:x.height}},`edit-multi-live-${h}`)}):Pe.elementBoundingBoxes.map((u,h)=>(0,F.jsx)("div",{className:`${W.multiSelectOutline} ${W.enter}`,style:{left:u.x,top:u.y-Ze,width:u.width,height:u.height}},`edit-multi-${h}`)):(()=>{let u=ue&&document.contains(ue)?ue.getBoundingClientRect():null,h=u?{x:u.left,y:u.top,width:u.width,height:u.height}:Pe.boundingBox?{x:Pe.boundingBox.x,y:Pe.isFixed?Pe.boundingBox.y:Pe.boundingBox.y-Ze,width:Pe.boundingBox.width,height:Pe.boundingBox.height}:null;return h?(0,F.jsx)("div",{className:`${Pe.isMultiSelect?W.multiSelectOutline:W.singleSelectOutline} ${W.enter}`,style:{left:h.x,top:h.y,width:h.width,height:h.height,...Pe.isMultiSelect?{}:{borderColor:"color-mix(in srgb, var(--agentation-color-accent) 60%, transparent)",backgroundColor:"color-mix(in srgb, var(--agentation-color-accent) 5%, transparent)"}}}):null})(),(0,F.jsx)(Di,{ref:s_,element:Pe.element,selectedText:Pe.selectedText,computedStyles:d2(Pe.computedStyles),placeholder:"Edit your feedback...",initialValue:Pe.comment,submitLabel:"Save",onSubmit:vm,onCancel:wm,onDelete:()=>Va(Pe.id),isExiting:mm,lightMode:!ro,accentColor:Pe.isMultiSelect?"var(--agentation-color-green)":"var(--agentation-color-accent)",style:(()=>{let u=Pe.isFixed?Pe.y:Pe.y-Ze;return{left:Math.max(160,Math.min(window.innerWidth-160,Pe.x/100*window.innerWidth)),...u>window.innerHeight-290?{bottom:window.innerHeight-u+20}:{top:u+20}}})()})]}),xo&&(0,F.jsxs)(F.Fragment,{children:[(0,F.jsx)("div",{ref:Pl,className:W.dragSelection}),(0,F.jsx)("div",{ref:Tl,className:W.highlightsContainer})]})]})]}),document.body)}export{nm as AG,Yx as R,Xx as RD};
