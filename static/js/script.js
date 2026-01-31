let map;
let markers = [];

const temples = {
    mahakaleshwar: [23.1828, 75.7680],
    sabarimala: [9.4333, 77.0800],
    kashi: [25.3109, 83.0107],
    tirupati: [13.6833, 79.3474]
};

const templeImages = {
    mahakaleshwar: "/static/mahakaleshwar.jpg",
    sabarimala: "/static/sabarimala.jpg",
    kashi: "/static/kashi.jpg",
    tirupati: "/static/tirupati.jpg"
};

document.addEventListener("DOMContentLoaded", function () {
    map = L.map('map').setView(temples.mahakaleshwar, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    changeTemple();
});

const colorMap = {
    hospital: "blue",
    medical: "red",
    hotel: "yellow",
    parking: "green",
    restaurant: "orange",
    railway: "black",
    metro: "purple",
    bus: "brown"
};

function getIcon(color) {
    return L.divIcon({
        html: `<div style="background:${color};
        width:14px;height:14px;border-radius:50%;
        border:2px solid black"></div>`
    });
}

function changeTemple() {
    let temple = document.getElementById("templeSelect").value;
    map.setView(temples[temple], 13);
    map.invalidateSize();
    document.getElementById("templeImage").src = templeImages[temple];

    markers.forEach(m => map.removeLayer(m));
    markers = [];

    fetch(`/temple-places?temple=${temple}`)
        .then(res => res.json())
        .then(data => {
            data.forEach(p => {
                let color = colorMap[p.category] || "gray";
                let marker = L.marker([p.lat, p.lon], {icon: getIcon(color)})
                    .addTo(map)
                    .bindPopup(`${p.tags.name || p.category}`);
                markers.push(marker);
            });
        });
}