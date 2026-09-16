import React from "react";
export default class ErrorBoundary extends React.Component{
 constructor(p){super(p);this.state={error:null};}
 static getDerivedStateFromError(error){return {error};}
 componentDidCatch(error,info){console.error("EESAG UI error",error,info);}
 render(){ if(this.state.error)return <div className="carte console-error"><h3>Cette page a rencontré une erreur</h3><p>Rechargez la page. Les autres espaces EESAG restent accessibles.</p><button className="btn" onClick={()=>window.location.reload()}>Recharger</button></div>; return this.props.children;}
}
