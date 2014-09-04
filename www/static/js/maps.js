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
	var int_begin = Math.ceil(begin);
	var int_end = Math.floor(end);
	if (int_begin > begin) {
		var ratio = 1. - (int_begin - begin); // in ]0;1[
		var latitude = (1 - ratio) * path[int_begin-1]['lat'] + ratio * path[int_begin]['lat'];
		var longitude = (1 - ratio) * path[int_begin-1]['long'] + ratio * path[int_begin]['long'];
		var pt = new google.maps.LatLng(latitude, longitude);
		map_pts.push(pt);
	}
	for (var i=int_begin ; i!=int_end ; i++) {
		var pt = new google.maps.LatLng(path[i]['lat'], path[i]['long']);
		map_pts.push(pt);
	}
	if (int_end < end) {
		var ratio = end - int_end; // in ]0;1[
		var latitude = (1 - ratio) * path[int_end-1]['lat'] + ratio * path[int_end]['lat'];
		var longitude = (1 - ratio) * path[int_end-1]['long'] + ratio * path[int_end]['long'];
		var pt = new google.maps.LatLng(latitude, longitude);
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
var lastPolyline = null;
var marker_begin = null, marker_end = null;

function updateMap(map, path, from, message_from, to, message_to, color) {
	// Remove the line and the markers
	if (lastPolyline)
		lastPolyline.setMap(null);
	if (marker_begin)
		marker_begin.setMap(null);
	if (marker_end)
		marker_end.setMap(null);

	if (from >= to)
		return;

	// Get the new one
	var map_pts = buildPath(path, from, to);
	if (color == undefined)
		lastPolyline = new google.maps.Polyline({
				path: map_pts,
				strokeColor: "#0000FF",
				strokeOpacity: 0.5,
				strokeWeight: 2
		});
	else
		lastPolyline = new google.maps.Polyline({
				path: map_pts,
				strokeColor: color,
				strokeOpacity: 0.5,
				strokeWeight: 3
		});
	lastPolyline.setMap(map);

	marker_begin = createMarker(map_pts[0], null);
	marker_begin.setMap(map);
	addInfoToMarker(map, marker_begin, message_from == null ? "Début" : message_from);

	marker_end = createMarker(map_pts[map_pts.length -1], null);
	marker_end.setMap(map);
	addInfoToMarker(map, marker_end, message_to == null ? "Fin" : message_to);
}
