// Custom sort method
Array.prototype.sortOnColumn = function(column, data_type) {
	this.sort(function(a, b){
		if(a[column] < b[column]){
			return -1;
		} else if(a[column] > b[column]) {
			return 1;
		}
		return 0;
	});
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
	} else if (content == "distance" || content == "speed") {
		var distance_km = rawdata/1000.;
		var distance_remaining_100m = parseInt(10*distance_km)%10;
		if (content == "distance")
			return Math.floor(distance_km) + ","
					+ distance_remaining_100m + " km";
		else if (content == "distance")
			return Math.floor(distance_km) + ","
					+ distance_remaining_100m + " km/h";
		
		return Math.floor(distance_km) + "," + distance_remaining_100m;
	} else
		return rawdata;
}

// Contains all the SortedTable that have been initialized
// by calling init()
var list_sortedtables = [];

function SortedTable(table, rawdata_details, rawdata) {
	// HTML element to sort
	this.table = table;

	// Give details concerning the input data:
	//  type: Specify which kind of data is available in each column
	//        types are: int, text, date, time..
	//  unit: show a particular unit
	//  content: apply custom display depending on the content
	//        contents are: datetime, time, distance
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
			new_content.attr("href", "#");
			new_content.attr("data-sortedtable", my_id);
			new_content.attr("data-sortedtable-column", i);
			new_content.click(function() {
					var sortedtable_id = parseInt($(this).attr("data-sortedtable"));
					var column_id = parseInt($(this).attr("data-sortedtable-column"));
					list_sortedtables[sortedtable_id].update(column_id);
			});
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
		// Sort the array
		this.rawdata.sortOnColumn(order_on_column);

		// Display the data
		tbody = $(table.getElementsByTagName("tbody")[0]);
		tbody.html("");
		for (var i=0 ; i!=this.rawdata.length ; i++) {
			var tr = $("<tr/>");
			for (var j=0 ; j!=this.rawdata_details.length +1 ; j++) {
				var td = $("<td/>");
				if (j > 0) {
					if ("unit" in this.rawdata_details[j-1])
						td.html(this.rawdata[i][j] + " "
								+ this.rawdata_details[j-1]["unit"]);
					else if ("content" in this.rawdata_details[j-1])
						td.html(formatSortedTableData(this.rawdata[i][j],
								this.rawdata_details[j-1]["content"]));
					else
						td.html(this.rawdata[i][j]);
				} else
					td.html(this.rawdata[i][j]);
				tr.append(td);
			}
			tbody.append(tr);
		}
	};
}
