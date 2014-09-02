var mapProp = {
	mapTypeId: google.maps.MapTypeId.ROADMAP,
};

var pinColor = "FE7596";
var pinImage = new google.maps.MarkerImage("http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|" + pinColor,
		new google.maps.Size(21, 34),
		new google.maps.Point(0,0),
		new google.maps.Point(10, 34));

function createMarker(latlong, icon) {
	if (icon)
		return new google.maps.Marker({position: latlong, icon: icon,});
	else
		return new google.maps.Marker({position: latlong,});
}

function addInfoToMarker(map, marker, message) {
	var infowindow = new google.maps.InfoWindow({content: message,});
	google.maps.event.addListener(marker, 'click', function() {
			infowindow.open(map, marker);
	});
}

function buildPath(path, begin, end) { // begin to end (included)
	if (begin == undefined) begin = 0;
	if (end == undefined) end = path.length;
	else end++;
	if (begin >= end-1) return [];
	var map_pts = [];
	for (var i=begin ; i!=end ; i++) {
		var pt = new google.maps.LatLng(path[i]['lat'], path[i]['long']);
		map_pts.push(pt);
	}
	return map_pts;
}

function getBounds(path) {
	var bounds = new google.maps.LatLngBounds();
	for (var i=0 ; i!=path.length ; i++) {
		var pt = new google.maps.LatLng(path[i]['lat'], path[i]['long']);
		bounds.extend(pt);
	}
	return bounds;
}

function adaptMap(map, path) {
	var bounds = getBounds(path);
	map.fitBounds(bounds);
	map.panToBounds(bounds);
}
