var selected_loc = "";
var k_means, shortest_paths, gen_pmedian;

function show_amsterdam() {
    centroids.clearLayers();
    clusters.clearLayers();
    selected_loc = "Amsterdam";
    basemap.panTo(new L.LatLng(52.392, 4.924));
    basemap.setZoom(14);
    document.getElementById('subHeader1').innerHTML = selected_loc;
    document.getElementById('subHeader2').innerHTML = "choose Algorithm or optimal Solution";
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
}

function show_seattle() {
    centroids.clearLayers();
    clusters.clearLayers();
    selected_loc = "Seattle";
    basemap.panTo(new L.LatLng(47.7031, -122.3253));
    basemap.setZoom(14);
    document.getElementById('subHeader1').innerHTML = selected_loc;
    document.getElementById('subHeader2').innerHTML = "choose Algorithm or optimal Solution";
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
}

function show_davutpasa() {
    centroids.clearLayers();
    clusters.clearLayers();
    selected_loc = "Davutpasa";
    basemap.panTo(new L.LatLng(41.0255, 28.8900));
    basemap.setZoom(15);
    document.getElementById('subHeader1').innerHTML = selected_loc;
    document.getElementById('subHeader2').innerHTML = "choose Algorithm or optimal Solution";
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
}


function show_kmeans() {
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
    document.getElementById('subHeader2').innerHTML = "K-Means Algorithm";
    centroids.clearLayers();
    clusters.clearLayers();
    switch (selected_loc) {
        case "Amsterdam":
            k_means = amsterdam_k_means;
            break;
        case "Seattle":
            k_means = seattle_k_means;
            break;
        case "Davutpasa":
            k_means = davutpasa_k_means;
            break;
        default:
            k_means = { "features": [] };
    }
    L.geoJSON(k_means, {
        pointToLayer: function(feature, latlng) {
            // return L.marker(latlng, {icon: ComunidadeIcon});
            return L.circle(latlng, {
                color: 'black',
                fillColor: determineFillColor(feature.properties.clusternumber),
                weight: determineColor(feature.properties.charging_station),
                fillOpacity: 1,
                radius: determineRadius(feature.properties.charging_station),
            })

        },
        onEachFeature: onEachFeature
    }).addTo(basemap);
}

function show_sp() {
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
    document.getElementById('subHeader2').innerHTML = "Betweenness Centrality based Algorithm";
    centroids.clearLayers();
    clusters.clearLayers();
    switch (selected_loc) {
        case "Amsterdam":
            shortest_paths = amsterdam_shortest_paths;
            break;
        case "Seattle":
            shortest_paths = seattle_shortest_paths;
            break;
        case "Davutpasa":
            shortest_paths = davutpasa_shortest_paths;
            break;
        default:
            shortest_paths = { "features": [] };
    }
    L.geoJSON(shortest_paths, {
        pointToLayer: function(feature, latlng) {
            // return L.marker(latlng, {icon: ComunidadeIcon});
            return L.circle(latlng, {
                color: 'black',
                fillColor: determineFillColor(feature.properties.clusternumber),
                weight: determineColor(feature.properties.charging_station),
                fillOpacity: 1,
                radius: determineRadius(feature.properties.charging_station),
            })

        },
        onEachFeature: onEachFeature
    }).addTo(basemap);
}

function show_pmedian() {
    document.getElementById("legend-1").style.display = "block";
    document.getElementById("legend-2").style.display = "none";
    document.getElementById('subHeader2').innerHTML = "Genetic P-Median Algorithm";
    centroids.clearLayers();
    clusters.clearLayers();
    switch (selected_loc) {
        case "Amsterdam":
            gen_pmedian = amsterdam_gen_pmedian;
            break;
        case "Seattle":
            gen_pmedian = seattle_gen_pmedian;
            break;
        case "Davutpasa":
            gen_pmedian = davutpasa_gen_pmedian;
            break;
        default:
            gen_pmedian = { "features": [] };
    }
    L.geoJSON(gen_pmedian, {
        pointToLayer: function(feature, latlng) {
            // return L.marker(latlng, {icon: ComunidadeIcon});
            return L.circle(latlng, {
                color: 'black',
                fillColor: determineFillColor(feature.properties.clusternumber),
                weight: determineColor(feature.properties.charging_station),
                fillOpacity: 1,
                radius: determineRadius(feature.properties.charging_station),
            })

        },
        onEachFeature: onEachFeature
    }).addTo(basemap);
}

function show_optimal() {
    document.getElementById("legend-1").style.display = "none";
    document.getElementById("legend-2").style.display = "block";
    document.getElementById('subHeader2').innerHTML = "Optimal Solution";
    centroids.clearLayers();
    clusters.clearLayers();
    switch (selected_loc) {
        case "Amsterdam":
            gen_pmedian = amsterdam_optimal;
            break;
        case "Seattle":
            gen_pmedian = seattle_optimal;
            break;
        case "Davutpasa":
            gen_pmedian = davutpasa_optimal;
            break;
        default:
            gen_pmedian = { "features": [] };
    }
    L.geoJSON(gen_pmedian, {
        pointToLayer: function(feature, latlng) {
            // return L.marker(latlng, {icon: ComunidadeIcon});
            return L.circle(latlng, {
                color: 'black',
                fillColor: determineFillColor(feature.properties.clusternumber),
                weight: determineColor(feature.properties.charging_station),
                fillOpacity: 1,
                radius: determineRadius(feature.properties.charging_station),
            })

        },
        onEachFeature: onEachFeature
    }).addTo(basemap);
}
