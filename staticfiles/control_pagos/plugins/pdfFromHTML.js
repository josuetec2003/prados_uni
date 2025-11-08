function HTMLtoPDF(nombre){
  nombre = nombre.replace(" ", "-");
  nombre = nombre.replace(" ", "-");
  nombre = nombre.replace(" ", "-").toLowerCase();

  var pdf = new jsPDF('p', 'pt', 'letter');

  pdf.setFontSize(8);

  source = $('#HTMLtoPDF')[0];

  specialElementHandlers = {
  	'#bypassme': function(element, renderer){
  		return true
  	}
  }

  margins = {
    top: 30,
    left: 30,
    right: 30,
    width: 600
  };

  pdf.fromHTML(
    	source,
      margins.left, // x coord
    	margins.top, // y coord
    	{
    		'width': margins.width, // max width of content on PDF
    		'elementHandlers': specialElementHandlers
    	},
    	function (dispose) {
  	  // dispose: object with X, Y of the last line add to the PDF
  	  //          this allow the insertion of new lines after html
        pdf.save(nombre + '.pdf');
      }
    )
}
