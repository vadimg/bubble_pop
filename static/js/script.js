function drawChart(api) {
    var url = '/api/' + api;
    $.get(url, function(data) {
        var obj = JSON.parse(data);

        var opts = {
            lines: { show: true },
        };

        var ret = mapData(obj, opts);

        $.plot($("#chart"), [ret], opts);
    });
}
