// baseline kmeans

var map_baseline_kmeans = L.map('map', {
    center: [52.392, 4.924],
    zoom: 14,
    minZoom: 2,
    maxZoom: 18,
});


var basemap_baseline_kmeans = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
opacity: 0.4,
}).addTo(basemap);


// https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
var FillColors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#023644', '#595d5e']

function determineFillColor(label) {
    return FillColors[label]
}

function determineColor(centroid) {
  if ( centroid ===  0) {
    return 0.5;
  } else {
    return 2.5;
  }
}

function determineZIndex(centroid) {
    if (centroid === 0) {
        return -1;
    } else {
        return 100;
    }
}

var amsterdam_centroids = L.layerGroup([]);
var amsterdam_clusters = L.layerGroup([]);


function onEachFeature(feature, layer) {
  var popupContent = "<p>amenity: " + feature.properties.amenity + "<br>centroid: " + feature.properties.centroid + "<br>id: " + feature.properties.id + "<br>label: " + feature.properties.label + "</p>";
  layer.bindPopup(popupContent);
  if (feature.properties.centroid === 1){
      amsterdam_centroids.addLayer(layer);
      layer.setStyle({pane: 'pane'+ 1});
      var currentPane = map_baseline_kmeans.createPane('pane' + 1);
      currentPane.style.zIndex = 650;
  }
  if (feature.properties.centroid === 0) {
      amsterdam_clusters.addLayer(layer);
  }
}

var amsterdam = L.geoJson(amsterdam_kmeans, {
  pointToLayer: function (feature, latlng) {
    // return L.marker(latlng, {icon: ComunidadeIcon});
    return L.circle(latlng, {
        color: 'black',
        fillColor: determineFillColor(feature.properties.label),
        weight: determineColor(feature.properties.centroid),
        fillOpacity: 1,
        radius: 25,
        })

  },
  onEachFeature: onEachFeature
})


// create array of Layers
var overlays = {
    "Charging Stations" : amsterdam_centroids,
    "All POIs" : amsterdam_clusters,
}

// Add layer control
L.control.layers(null, overlays).addTo(map_baseline_kmeans);

map_baseline_kmeans.addLayer(amsterdam_centroids);
map_baseline_kmeans.addLayer(amsterdam_clusters);

// baseline shortest paths

var map_baseline_sp = L.map('map_baseline_sp', {
    center: [52.392, 4.924],
    zoom: 14,
    minZoom: 2,
    maxZoom: 18,
});


var basemap_sp = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
opacity: 0.4,
}).addTo(map_baseline_sp);

var amsterdam_centroids_sp = L.layerGroup([]);
var amsterdam_clusters_sp = L.layerGroup([]);


var amsterdam_baseline_sp = L.geoJson(amsterdam_baseline_sp, {
  pointToLayer: function (feature, latlng) {
    // return L.marker(latlng, {icon: ComunidadeIcon});
    return L.circle(latlng, {
        color: 'black',
        fillColor: determineFillColor(feature.properties.label),
        weight: determineColor(feature.properties.centroid),
        fillOpacity: 1,
        radius: 25,
        })

  },
  onEachFeature: onEachFeature_baseline_sp
})


function onEachFeature_baseline_sp(feature, layer) {
  var popupContent = "<p>amenity: " + feature.properties.amenity + "<br>centroid: " + feature.properties.centroid + "<br>id: " + feature.properties.id + "<br>label: " + feature.properties.label + "</p>";
  layer.bindPopup(popupContent);
  if (feature.properties.centroid === 1){
      amsterdam_centroids_sp.addLayer(layer);
      layer.setStyle({pane: 'pane'+ 1});
      var currentPane = map_baseline_sp.createPane('pane' + 1);
      currentPane.style.zIndex = 650;
  }
  if (feature.properties.centroid === 0) {
      amsterdam_clusters_sp.addLayer(layer);
  }
}

var overlays_baseline_sp = {
    "Charging Stations" : amsterdam_centroids_sp,
    "All POIs" : amsterdam_clusters_sp,
}

L.control.layers(null, overlays_baseline_sp).addTo(map_baseline_sp);
map_baseline_sp.addLayer(amsterdam_centroids_sp);
map_baseline_sp.addLayer(amsterdam_clusters_sp);



// pmedian genetic algorithm

var map_pmedian = L.map('map_pmedian', {
    center: [52.392, 4.924],
    zoom: 14,
    minZoom: 2,
    maxZoom: 18,
});


var basemap_pmedian = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
opacity: 0.4,
}).addTo(map_pmedian);

var amsterdam_centroids_pmedian = L.layerGroup([]);
var amsterdam_clusters_pmedian = L.layerGroup([]);


var amsterdam_pmedian = L.geoJson(amsterdam_pmedian, {
  pointToLayer: function (feature, latlng) {
    // return L.marker(latlng, {icon: ComunidadeIcon});
    return L.circle(latlng, {
        color: 'black',
        fillColor: determineFillColor(feature.properties.label),
        weight: determineColor(feature.properties.centroid),
        fillOpacity: 1,
        radius: 25,
        })

  },
  onEachFeature: onEachFeature_pmedian
})


function onEachFeature_pmedian(feature, layer) {
  var popupContent = "<p>amenity: " + feature.properties.amenity + "<br>centroid: " + feature.properties.centroid + "<br>id: " + feature.properties.id + "<br>label: " + feature.properties.label + "</p>";
  layer.bindPopup(popupContent);
  if (feature.properties.centroid === 1){
      amsterdam_centroids_pmedian.addLayer(layer);
      layer.setStyle({pane: 'pane'+ 1});
      var currentPane = map_pmedian.createPane('pane' + 1);
      currentPane.style.zIndex = 650;
  }
  if (feature.properties.centroid === 0) {
      amsterdam_clusters_pmedian.addLayer(layer);
  }
}

var overlays_pmedian = {
    "Charging Stations" : amsterdam_centroids_pmedian,
    "All POIs" : amsterdam_clusters_pmedian,
}

L.control.layers(null, overlays_pmedian).addTo(map_pmedian);
map_pmedian.addLayer(amsterdam_centroids_pmedian);
map_pmedian.addLayer(amsterdam_clusters_pmedian);
