const brPlugin = {
  "after:highlightElement": ({ el, result, text }) => {
    //console.log(el);
    //console.log(el.childNodes)
    var space_re = new RegExp("^ +$");
    el.childNodes.forEach((node, idx)=>{
      if (node.nodeName == '#text' && node.nodeValue.match(space_re)){
        if (idx > 0) {
            el.childNodes[idx-1].innerHTML = el.childNodes[idx-1].innerHTML + node.nodeValue;
        }
        else {
            el.childNodes[idx+1].innerHTML = node.nodeValue + el.childNodes[idx+1].innerHTML;
        }

      }
    })
    el.innerHTML = el.innerHTML.replace(/\n/g, '<br>');
  }
};

hljs.addPlugin(brPlugin);
hljs.highlightAll();

var clipboard = new ClipboardJS('.btn');

clipboard.on('success', function(e) {
  console.info('Copy successfully.')
  console.info('Action:', e.action);
  console.info('Trigger:', e.trigger);

  e.clearSelection();
});

clipboard.on('error', function(e) {
  console.error('Action:', e.action);
  console.error('Trigger:', e.trigger);
});