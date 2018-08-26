//File: main.js
//Date: Sun Jan 11 23:32:26 2015 +0800
//Author: Yuxin Wu

var playVoice = function(event) {
  var target = event.target;
  while (!target.classList.contains('cloud'))
    target = target.parentElement;
  var audio = target.getElementsByTagName('audio')[0];
  audio.play();
};

$(document).ready(function() {
   $(".fancybox").fancybox({
    // fancybox will otherwise scroll page to top
    helpers: { overlay : { locked : false}}
   });

   // use small_img for big_img, or big for small
   $('.fancybox').each(function(idx, d) {
     var LEN_THRES = 40;
     var big_img = d.getAttribute('href'),
     small_img = d.children[0].src;
     if (small_img.length > LEN_THRES &&
             big_img.length < LEN_THRES)
       d.setAttribute('href', small_img);
   });
 });
