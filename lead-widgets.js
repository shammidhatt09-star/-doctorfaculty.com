(function(){
  var SS_POPUP_KEY = 'df_popup_shown_v1';
  var SS_BAR_KEY = 'df_bar_dismissed_v1';

  var overlay = document.getElementById('dfPopupOverlay');
  var popupClose = document.getElementById('dfPopupClose');
  var leftTab = document.getElementById('dfLeftTab');
  var bar = document.getElementById('dfBottomBar');
  var barCta = document.getElementById('dfBottomBarCta');
  var barClose = document.getElementById('dfBottomBarClose');

  function openPopup(){
    if(!overlay) return;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    try{ sessionStorage.setItem(SS_POPUP_KEY, '1'); }catch(e){}
  }
  function closePopup(){
    if(!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = '';
  }

  if(popupClose) popupClose.addEventListener('click', closePopup);
  if(overlay) overlay.addEventListener('click', function(e){ if(e.target === overlay) closePopup(); });
  if(leftTab){
    leftTab.addEventListener('click', openPopup);
    leftTab.addEventListener('keypress', function(e){ if(e.key === 'Enter' || e.key === ' ') openPopup(); });
  }
  if(barCta) barCta.addEventListener('click', openPopup);
  if(barClose){
    barClose.addEventListener('click', function(){
      if(bar) bar.style.display = 'none';
      try{ sessionStorage.setItem(SS_BAR_KEY, '1'); }catch(e){}
    });
  }

  try{
    if(sessionStorage.getItem(SS_BAR_KEY) === '1' && bar) bar.style.display = 'none';
  }catch(e){}

  var triggered = false;
  function maybeAutoOpen(){
    if(triggered) return;
    try{ if(sessionStorage.getItem(SS_POPUP_KEY) === '1'){ triggered = true; return; } }catch(e){}
    triggered = true;
    openPopup();
  }
  setTimeout(maybeAutoOpen, 12000);
  window.addEventListener('scroll', function(){
    var doc = document.documentElement;
    var scrolled = (window.scrollY + window.innerHeight) / doc.scrollHeight;
    if(scrolled > 0.5) maybeAutoOpen();
  }, { passive: true });

  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closePopup();
  });
})();
