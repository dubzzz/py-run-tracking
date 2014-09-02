// Custom sort method
Array.prototype.sortOnColumn = function(column, reversed=false) {
	this.sort(function(a, b){
		if(a[column] < b[column]){
			return reversed ? 1 : -1;
		} else if(a[column] > b[column]) {
			return reversed ? -1 : 1;
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
	} else if (content == "distance") { // in meters
		var distance_km = rawdata/1000.;
		var distance_remaining_100m = parseInt(10*distance_km)%10;
		return Math.floor(distance_km) + ","
				+ distance_remaining_100m + " km";
	} else if (content == "speed") { // in m/s
		var speed_kmh = 3.6*rawdata;
		var speed_remaining_100kmh = parseInt(10*speed_kmh)%10;
		return Math.floor(speed_kmh) + ","
				+ speed_remaining_100kmh + " km/h";
	} else if (content == "date") { // in unix time seconds
		var to_date = new Date(1000*rawdata);
		
		var day_str = to_date.getDate() < 10 ? "0" + to_date.getDate()
				: to_date.getDate().toString();
		var month_str = to_date.getMonth() < 10 ? "0" + to_date.getMonth()
				: to_date.getMonth().toString();
		var year_str = to_date.getFullYear().toString();
		return day_str + "/" + month_str + "/" + year_str;
	} else if (content == "datetime") { // in unix time seconds
		var to_date = new Date(1000*rawdata);
		
		var day_str = to_date.getDate() < 10 ? "0" + to_date.getDate()
				: to_date.getDate().toString();
		var month_str = to_date.getMonth() < 10 ? "0" + to_date.getMonth()
				: to_date.getMonth().toString();
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
				var td = $("<td/>");
				if (j > 0) {
					if ("unit" in this.rawdata_details[j-1]) {
						if (this.rawdata_details[j-1]["type"] == "int")
							td.html(formatSortedTableData(this.rawdata[i][j],
									"thousands") + " "
									+ this.rawdata_details[j-1]["unit"]);
						else
							td.html(this.rawdata[i][j] + " "
									+ this.rawdata_details[j-1]["unit"]);
					} else if ("content" in this.rawdata_details[j-1])
						td.html(formatSortedTableData(this.rawdata[i][j],
								this.rawdata_details[j-1]["content"]));
					else if (this.rawdata_details[j-1]["type"] == "int")
						td.html(formatSortedTableData(this.rawdata[i][j],
								"thousands"));
					else
						td.html(this.rawdata[i][j]);
				} else
					td.html(formatSortedTableData(this.rawdata[i][j],
							"thousands"));
				tr.append(td);
			}
			tbody.append(tr);
		}
	};
}
