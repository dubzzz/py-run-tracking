// Custom sort method
Array.prototype.sortOnColumn = function(column, reversed) {
	this.sort(function(a, b){
		if(a[column] < b[column]){
			return reversed ? 1 : -1;
		} else if(a[column] > b[column]) {
			return reversed ? -1 : 1;
		}
		return 0;
	});
}

function numberToString(number, num_decimals) {
	var power = Math.pow(10, num_decimals);
	var number_bis = Math.round(number * power);
	
	var returned_txt = Math.floor(number_bis/power) + ",";
	
	var decimals = number_bis%power;
	var missing_decimals = num_decimals
			- (decimals == 0 ? 1 : Math.ceil(Math.log10(decimals+1)));
	for (var i=0 ; i!= missing_decimals ; i++) {
		returned_txt += "0";
	}
	return returned_txt + decimals;
}

function formatSortedTableData(rawdata, content) {
	if (content == "time") { // in seconds
		var hours = Math.floor(rawdata/3600);
		rawdata -= 3600 * hours;
		var minutes = Math.floor(rawdata/60);
		rawdata -= 60 * minutes;
		var minutes_txt = minutes < 10 ? "0"+minutes : minutes.toString();
		var seconds = parseInt(rawdata);
		var seconds_txt = seconds < 10 ? "0"+seconds : seconds.toString();
		return hours + ":" + minutes_txt + ":" + seconds_txt;
	} else if (content == "distance") { // in meters
		return numberToString(rawdata/1000., 1) + " km";
	} else if (content == "speed") { // in m/s
		return numberToString(3.6*rawdata, 1) + " km/h";
	} else if (content == "date") { // in unix time seconds
		var to_date = new Date(1000*rawdata);
		
		var day_str = to_date.getDate() < 10 ? "0" + to_date.getDate()
				: to_date.getDate().toString();
		var month_str = to_date.getMonth()+1 < 10 ? "0" + (to_date.getMonth()+1)
				: (to_date.getMonth()+1).toString();
		var year_str = to_date.getFullYear().toString();
		return day_str + "/" + month_str + "/" + year_str;
	} else if (content == "datetime") { // in unix time seconds
		var to_date = new Date(1000*rawdata);
		
		var day_str = to_date.getDate() < 10 ? "0" + to_date.getDate()
				: to_date.getDate().toString();
		var month_str = to_date.getMonth()+1 < 10 ? "0" + (to_date.getMonth()+1)
				: (to_date.getMonth()+1).toString();
		var year_str = to_date.getFullYear().toString();
		var hours_str = to_date.getHours() < 10 ? "0" + to_date.getHours()
				: to_date.getHours().toString();
		var minutes_str = to_date.getMinutes() < 10 ? "0" + to_date.getMinutes()
				: to_date.getMinutes().toString();
		var seconds_str = to_date.getSeconds() < 10 ? "0" + to_date.getSeconds()
				: to_date.getSeconds().toString();
		return day_str + "/" + month_str + "/" + year_str
				+ " " + hours_str + ":" + minutes_str + ":" + seconds_str;
	} else if (content == "thousands") { // integer
		var current = parseInt(rawdata);
		var text = "";
		while (current != 0 || text.length == 0) {
			var current_group = current % 1000;
			current = Math.floor(current/1000);
			
			if (text.length != 0)
				text = " " + text;
			
			if (current == 0)
				text = current_group.toString() + text;
			else if (current_group < 10)
				text = "00" + current_group.toString() + text;
			else if (current_group < 100)
				text = "0" + current_group.toString() + text;
			else
				text = current_group.toString() + text;
		}
		return text;
	} else if (content == "url") {
		return '<a href="' + encodeURI(rawdata) + '"><span class="glyphicon glyphicon-eye-open"></span></a>';
	} else // html is in this case
		return rawdata;
}

var known_content_format = [
		"time", "distance", "speed", "date", "datetime",
		"thousands", "url", "html",
];
var known_content_funny_values = {
		calories: [
			{value: 12.025, name: "M&M's",},
			{value: 180, name: "Croissant", plural: "Croissants"},
			{value: 509, name: "Big Mac"},
		],
		distance: [
			{value: 346, name: "Tour de stade de football", plural: "Tours de stade de football"},
			{value: 50000, name: "Lyon - St Etienne"},
			{value: 394000, name: "Paris - Lyon"},
		],
};	

// Contains all the SortedTable that have been initialized
// by calling init()
var list_sortedtables = [];

function addTooltipIfPossible(jquery_element, value, content) {
	// Unknown content for funny values
	if (!(content in known_content_funny_values))
		return;
	
	var funny_txt = "";
	var funny_details = known_content_funny_values[content];
	for (var i=0 ; i!=funny_details.length ; i++) {
		var num_funny = value/funny_details[i]['value'];
		if (num_funny >= 0.005) {
			funny_txt += '<tr>';
			funny_txt += '<td>' + numberToString(num_funny, 2) + '</td>';
			funny_txt += '<td>'
				+ ((num_funny > 1 && 'plural' in funny_details[i])
					? funny_details[i]['plural']
					: funny_details[i]['name'])
				+ '</td>';
			funny_txt += '</tr>';
		}
	}
	if (funny_txt.length != 0) {
		funny_txt = '<table>' + funny_txt + '</table>';
		jquery_element.tooltip({content: funny_txt, items: "*",
				show: false, hide: false, track: true});
	}
}

function getFormattedTD(rawdata, rawdata_details) {
	var td = $("<td/>");
	// If we have raw details
	if (rawdata_details != null) {
		// If a known content
		if ("content" in rawdata_details
				&& $.inArray(rawdata_details["content"], known_content_format) != -1) {
			td.html(formatSortedTableData(rawdata, rawdata_details["content"]));
		// No known content but a specified unit
		} else if ("unit" in rawdata_details) {
			if (rawdata_details["type"] == "int") {
				td.html(formatSortedTableData(rawdata, "thousands")
						+ " " + rawdata_details["unit"]);
			} else {
				td.html(rawdata + " " + rawdata_details["unit"]);
			}
		// No known content, no unit but an int
		} else if (rawdata_details["type"] == "int") {
			td.html(formatSortedTableData(rawdata, "thousands"));
		// Just a text
		} else {
			td.html(rawdata);
		}
		
		// Try to find if it can have a tooltip
		/*if ("content" in rawdata_details) {
			addTooltipIfPossible(td, rawdata, rawdata_details["content"]);
		}*/
	} else
		td.html(formatSortedTableData(rawdata, "thousands"));
	return td;
}

function SortedTable(table, rawdata_details, rawdata) {
	// HTML element to sort
	this.table = table;

	// Give details concerning the input data:
	//  type: Specify which kind of data is available in each column
	//        types are: int, text, date, time..
	//  unit: show a particular unit
	//  content: apply custom display depending on the content
	//        contents are: datetime, time, distance, html, url
	this.rawdata_details = rawdata_details;

	// The data that should be put in the table 
	this.rawdata = rawdata;

	this.init = function() {
		// Add links on columns
		var my_id = list_sortedtables.length;
		list_sortedtables.push(this);
		var head_columns = table.getElementsByTagName("thead")[0]
				.getElementsByTagName("td");
		for (var i=0 ; i!=head_columns.length ; i++) {
			var column = $(head_columns[i]);
			var content = column.html();
			var new_content = $("<a/>");
			new_content.html(content);
			new_content.attr("href", "javascript:void(0)");
			if (i == 0 || !("content" in this.rawdata_details[i-1]) ||
					("content" in this.rawdata_details[i-1] &&
						this.rawdata_details[i-1]["content"] != "url" &&
						this.rawdata_details[i-1]["content"] != "html")) {
				new_content.attr("data-sortedtable", my_id);
				new_content.attr("data-sortedtable-column", i);
				new_content.click(function() {
						var sortedtable_id = parseInt($(this).attr("data-sortedtable"));
						var column_id = parseInt($(this).attr("data-sortedtable-column"));
						list_sortedtables[sortedtable_id].update(column_id);
				});
			} else {
				new_content.attr("data-sortedtable-disabled", my_id);
				new_content.attr("data-sortedtable-column-disabled", i);
			}
			column.html(new_content);
		}

		// Add id to rawdata
		for (var i=0 ; i!=this.rawdata.length ; i++) {
			this.rawdata[i].unshift(i+1);
		}

		// Draw the table
		this.update(0);
	};
	this.update = function(order_on_column) {
		// Get previous order
		var head_columns = table.getElementsByTagName("thead")[0]
				.getElementsByTagName("td");
		var previous_order = $(head_columns[order_on_column]
				.getElementsByTagName("a")[0]).attr("data-sortedtable-order");
		var new_order = previous_order == "asc" ? "desc" : "asc";
		for (var i=0 ; i!=head_columns.length ; i++) {
			if (i == order_on_column)
				$(head_columns[i]
						.getElementsByTagName("a")[0])
							.attr("data-sortedtable-order", new_order);
			else
				$(head_columns[i]
						.getElementsByTagName("a")[0])
							.attr("data-sortedtable-order", "");
		}
		
		// Sort the array
		this.rawdata.sortOnColumn(order_on_column, new_order == "desc");

		// Display the data
		tbody = $(table.getElementsByTagName("tbody")[0]);
		tbody.html("");
		for (var i=0 ; i!=this.rawdata.length ; i++) {
			var tr = $("<tr/>");
			for (var j=0 ; j!=this.rawdata_details.length +1 ; j++) {
				var td = getFormattedTD(this.rawdata[i][j],
						j>0 ? this.rawdata_details[j-1] : null)
				tr.append(td);
			}
			tbody.append(tr);
		}
	};
}
