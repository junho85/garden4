function getAvatarImgUrl(user) {
    return `https://avatars.githubusercontent.com/${user}`;
}

function get_attendance() {
    let date = $("#date").val();

    $.ajax({
        method: "GET",
        url: "get/" + date,
        dataType: "JSON",
        data: {}
    }).done(function (data) {
        // console.log(data);
        let html = `<table class="table table-sm">
<thead>
<th>user</th>
<th>first_ts</th>
</thead>
<tbody>
`;
        $.each(data, function(index, row) {
            let first_ts = "";
            if (row.first_ts) {
                first_ts = moment(new Date(row.first_ts)).format("YYYY-MM-DD HH:mm:ss")
            }
            html += `<tr>`;
            html += `<td><a href="https://github.com/${row.user}" target="_blank">${row.user}</a></td>`;
            html += `<td>${first_ts}</td>`;
            html += `</tr>`;
        });

        html += "</tbody></table>";
        $("#attendance").html(html);
    }).fail(function (data) {
        console.log(data);
        alert("실패");
    });
}
