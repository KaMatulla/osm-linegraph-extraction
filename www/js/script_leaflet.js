var basemap = L.map('map', {
    center: [52.392, 4.924],
    zoom: 14,
    minZoom: 2,
    maxZoom: 18,
});


var basemap_layer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    opacity: 0.4,
}).addTo(basemap);


// https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
var fillColors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#023644', '#595d5e']

var centroids = L.layerGroup([]);
var clusters = L.layerGroup([]);

// create array of Layers
var overlays = {
    "Charging Stations" : centroids,
    "All POIs" : clusters,
}

var bounds_amsterdam = [[52.3815, 4.8996], [52.3998, 4.9541]];
var bounds_seattle = [[47.6862, -122.3616], [47.7200, -122.2890]];
var point_davutpasa_1 = new L.LatLng(41.03148252197906, 28.88460233254973);
var point_davutpasa_2 = new L.LatLng(41.02700638889392, 28.88460888826381);
var point_davutpasa_3 = new L.LatLng(41.02700218513624, 28.8850092731669);
var point_davutpasa_4 = new L.LatLng(41.02348366977374, 28.88501754494686);
var point_davutpasa_5 = new L.LatLng(41.02349856109988, 28.88671384190673);
var point_davutpasa_6 = new L.LatLng(41.0173965418209, 28.886733693177);
var point_davutpasa_7 = new L.LatLng(41.01740645736633, 28.89200915317861);
var point_davutpasa_8 = new L.LatLng(41.0194952918313, 28.89200801263461);
var point_davutpasa_9 = new L.LatLng(41.01950080099652, 28.89701574021168);
var point_davutpasa_10 = new L.LatLng(41.02439647423031, 28.89700906352102);
var point_davutpasa_11 = new L.LatLng(41.02440445158301, 28.89351840357554);
var point_davutpasa_12 = new L.LatLng(41.02929460644044, 28.89350149477178);
var point_davutpasa_13 = new L.LatLng(41.02930015980873, 28.89341402176818);
var point_davutpasa_14 = new L.LatLng(41.03010003045474, 28.89340966990799);
var point_davutpasa_15 = new L.LatLng(41.03010188341117, 28.88851440116131);
var point_davutpasa_16 = new L.LatLng(41.03149406843667, 28.88850184205533);
var point_davutpasa_17 = new L.LatLng(41.03148252197906, 28.88460233254973);

var bounds_davutpasa = [point_davutpasa_1, point_davutpasa_2, point_davutpasa_3,
                        point_davutpasa_4, point_davutpasa_5, point_davutpasa_6,
                        point_davutpasa_7, point_davutpasa_8, point_davutpasa_9,
                        point_davutpasa_10, point_davutpasa_11, point_davutpasa_12,
                        point_davutpasa_13, point_davutpasa_14, point_davutpasa_15,
                        point_davutpasa_16, point_davutpasa_17];

// var bounds_davutpasa = [[], []];
// create an orange rectangle
var boundingBox_amsterdam = L.rectangle(bounds_amsterdam, {color: "#000000", fillColor: '#f7af19', fillOpacity: 0, weight: 2});
var boundingBox_seattle = L.rectangle(bounds_seattle, {color: "#000000", fillColor: '#f7af19', fillOpacity: 0, weight: 2});
var polyline_davutpasa = new L.Polyline(bounds_davutpasa, {color: '#000000', weight: 2});


// var boundingBox_davutpasa = L.rectangle(bounds_davutpasa, {color: "#000000", fillColor: '#f7af19', fillOpacity: 0, weight: 1});
basemap.addLayer(boundingBox_amsterdam);
basemap.addLayer(boundingBox_seattle);
//basemap.addLayer(polyline_davutpasa);
polyline_davutpasa.addTo(basemap);
// basemap.addLayer(boundingBox_davutpasa);

window.onload = function() {
    var scale = 'scale(1.0)';
    document.body.style.webkitTransform = // Chrome, Opera, Safari
        document.body.style.msTransform = // IE 9
        document.body.style.transform = scale; // General
}


// Add layer control
L.control.layers(null, overlays).addTo(basemap);

basemap.addLayer(centroids);
basemap.addLayer(clusters);

function determineFillColor(label) {
    return fillColors[label]
}

function determineColor(centroid) {
    if (centroid === 0) {
        return 0.5;
    } else {
        return 2.5;
    }
}

function determineRadius(centroid) {
    if (centroid === 0) {
        return 25;
    } else {
        return 50;
    }
}

// function determineZIndex(centroid) {
//     if (centroid === 0) {
//         return -1;
//     } else {
//         return 100;
//     }
// }

function onEachFeature(feature, layer) {
    var popupContent = "<p>OSM-Keyword: " + feature.properties.osm_keyword + "<br>Charging Station (bool): " + feature.properties.charging_station + "<br>OSM-ID: " + feature.properties.osm_id + "<br>Clusternumber: " + feature.properties.clusternumber + "</p>";
    layer.bindPopup(popupContent);
    if (feature.properties.charging_station === 1) {
        centroids.addLayer(layer);
        // layer.setStyle({ pane: 'pane' + 1 });
        // var currentPane = basemap.createPane('pane' + 1);
        // currentPane.style.zIndex = 650;
    }
    if (feature.properties.charging_station === 0) {
        clusters.addLayer(layer);
    }
}


function zentroidFilter(feature, layer) {
    if (feature.properties.charging_station === 1) return true;
}
