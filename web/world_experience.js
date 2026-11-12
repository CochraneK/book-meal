(function(){
  "use strict";
  var nav=document.getElementById("world-list"),pane=document.getElementById("world-view");
  var search=document.getElementById("world-search"),live=document.getElementById("selection-status");
  if(!nav||!pane)return;
  function show(id,focus){
    if(!/^[a-z0-9-]+$/.test(id))return false;
    var template=document.getElementById("world-template-"+id);
    if(!template)return false;
    pane.replaceChildren(template.content.cloneNode(true));
    var options=nav.querySelectorAll("a[data-book]");
    for(var i=0;i<options.length;i++){
      if(options[i].getAttribute("data-book")===id)options[i].setAttribute("aria-current","page");
      else options[i].removeAttribute("aria-current");
    }
    var title=pane.querySelector("#world-title");
    document.title=(title?title.textContent:"书籍世界")+" · Book-Meal";
    if(live&&title)live.textContent="已切换至"+title.textContent;
    if(focus){
      try{history.pushState({book:id},"","?book="+encodeURIComponent(id));}catch(e){}
      if(title)title.focus({preventScroll:true});
    }
    return true;
  }
  nav.addEventListener("click",function(e){
    var a=e.target.closest("a[data-book]");
    if(a&&nav.contains(a)&&show(a.getAttribute("data-book"),true))e.preventDefault();
  });
  if(search)search.addEventListener("input",function(){
    var q=search.value.trim().toLowerCase(),found=0;
    var anchors=nav.querySelectorAll("a[data-book]");
    for(var i=0;i<anchors.length;i++){
      var visible=(anchors[i].getAttribute("data-search")||"").indexOf(q)>=0;
      anchors[i].hidden=!visible;
      if(visible)found++;
    }
    var empty=document.getElementById("world-empty");
    if(empty)empty.hidden=found>0;
  });
  window.addEventListener("popstate",function(){
    var requested=new URLSearchParams(location.search).get("book");
    show(requested||nav.querySelector("a[data-book]").getAttribute("data-book"),false);
  });
  var requested=new URLSearchParams(location.search).get("book");
  if(requested)show(requested,false);
})();
