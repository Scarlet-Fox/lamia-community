$ ->
  options = 
    $AutoPlay: true
    $AutoPlaySteps: 1
    $AutoPlayInterval: 10000
    $PauseOnHover: 1
    $FillMode: 1
    
    $ArrowNavigatorOptions:
      $Class: $JssorArrowNavigator$
      $ChanceToShow: 1
      
    $BulletNavigatorOptions:
      $Class: $JssorBulletNavigator$
      $ChanceToShow: 2
      $AutoCenter: 1
      $Steps: 1
      $Lanes: 1
      $SpacingX: 12
      $SpacingY: 4
      $Orientation: 1
      $Scale: false
    
  jssor_slider2= new $JssorSlider$("slider-container", options)
  
  ScaleSlider = () ->
    paddingWidth = 20
    minReserveWidth = 225
    parentElement = jssor_slider2.$Elmt.parentNode
    parentWidth = parentElement.clientWidth
    if parentWidth
      availableWidth = parentWidth - paddingWidth;
      sliderWidth = availableWidth * 0.7
      sliderWidth = Math.min(sliderWidth, 600)
      sliderWidth = Math.max(sliderWidth, 200)
      clearFix = "none";
      if availableWidth - sliderWidth < minReserveWidth
        sliderWidth = availableWidth
        sliderWidth = Math.max(sliderWidth, 200)
        clearFix = "both"

        $('#clearFixDiv').css('clear', clearFix);
        jssor_slider2.$ScaleWidth(sliderWidth);
      else
        window.setTimeout ScaleSlider, 30
  ScaleSlider()

  $(window).bind("load", ScaleSlider);
  $(window).bind("resize", ScaleSlider);
  $(window).bind("orientationchange", ScaleSlider);