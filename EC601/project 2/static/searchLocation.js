var currentMarker = null;
var currentInfoWindow = null;

function searchLocation() {
    // Create a new geocoder object from the Google Maps API
    var geocoder = new google.maps.Geocoder();
    
    // Get the value entered in the address input field by the user
    var address = document.getElementById("addressInput").value;

    // Remove the previous marker and info window if they exist
    if (currentMarker) {
        currentMarker.setMap(null);
        currentMarker = null;
    }
    if (currentInfoWindow) {
        currentInfoWindow.close();
        currentInfoWindow = null;
    }

    // Use the geocoder to convert the address into latitude and longitude
    geocoder.geocode({'address': address}, function(results, status) {
        if (status === 'OK') {
            var location = results[0].geometry.location;
            map.setCenter(location);
            map.setZoom(18);

            // Place a marker on the geocoded location
            var infoMarker = new google.maps.Marker({
                position: location,
                map: map
            });
            currentMarker = infoMarker; // Store the reference for next time

            // Create a PlacesService object
            var placesService = new google.maps.places.PlacesService(map);

            // Use the placeId from the geocoding result to get more details
            var detailsRequest = {
                placeId: results[0].place_id
            };

            placesService.getDetails(detailsRequest, function(place, status) {
                if (status == google.maps.places.PlacesServiceStatus.OK) {
                    var content = `<strong>${place.name || ''}</strong><br>
                                   ${place.formatted_address}<br>`;
                    if (place.photos && place.photos.length > 0) {
                        content += `<img src="${place.photos[0].getUrl({maxWidth: 200, maxHeight: 200})}" alt="${place.name || 'Location'}">`;
                    }
                    var infoWindow = new google.maps.InfoWindow({
                        content: content,
                        position: location,
                    });
                    infoWindow.open(map, infoMarker);
                    currentInfoWindow = infoWindow; // Store the reference for next time
                } else {
                    var infoWindow = new google.maps.InfoWindow({
                        content: results[0].formatted_address,
                        position: location,
                    });
                    infoWindow.open(map, infoMarker);
                    currentInfoWindow = infoWindow; // Store the reference for next time
                }
            });

        } else {
            alert('Search was not successful for the following reason: ' + status);
        }
    });
}
