// Global variables
var directionsService;
var drivingDirectionsRenderer;
var walkingDirectionsRenderer;
var bicyclingDirectionsRenderer;
var markers = [];
var infoWindows = [];
var isNavigationMode = false;
var infoMarker = null;
var geocoder = new google.maps.Geocoder();
var placesService;
var currentInfoWindow = null;

// Initialize navigation features and event listeners
function initNavigation() {
    // Create new directions service
    directionsService = new google.maps.DirectionsService();

    // Setup driving directions renderer with a blue polyline
    drivingDirectionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        preserveViewport: true,
        polylineOptions: { strokeColor: "blue" }
    });

    // Setup walking directions renderer with a green polyline
    walkingDirectionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        preserveViewport: true,
        polylineOptions: { strokeColor: "green" }
    });

    // Setup bicycling directions renderer with a red polyline
    bicyclingDirectionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        preserveViewport: true,
        polylineOptions: { strokeColor: "red" }
    });

    // Add map click event listener to call the selectLocation function
    google.maps.event.addListener(map, 'click', function(event) {
        selectLocation(event.latLng);
    });

    // Initialize places service
    placesService = new google.maps.places.PlacesService(map);
}

// Toggle between Navigation Mode and Info Mode
function toggleMode() {
    isNavigationMode = !isNavigationMode;
    if (isNavigationMode) {
        // If in Navigation Mode, change button text
        document.getElementById("modeToggle").innerText = "Switch to Info Mode";
        // Remove infoMarker if it exists
        if (infoMarker) {
            infoMarker.setMap(null);
            infoMarker = null;
        }
    } else {
        // If in Info Mode, change button text and reset navigation related features
        document.getElementById("modeToggle").innerText = "Switch to Navigation Mode";
        for (var marker of markers) {
            marker.setMap(null);
        }
        markers = [];
        drivingDirectionsRenderer.setDirections({ routes: [] });
        walkingDirectionsRenderer.setDirections({ routes: [] });
        bicyclingDirectionsRenderer.setDirections({ routes: [] });
    }
}

// Handle selecting a location on the map
function selectLocation(location) {
    if (isNavigationMode) {
        // If in Navigation Mode and already have two markers, remove the oldest one
        if (markers.length == 2) {
            markers[0].setMap(null);
            markers.shift();
        }

        // Create and place a new marker at the clicked location
        var marker = new google.maps.Marker({
            position: location,
            map: map
        });
        markers.push(marker);

        // Close all existing infoWindows
        for (var i = 0; i < infoWindows.length; i++) {
            infoWindows[i].close();
        }
        infoWindows = [];

        // If there are two markers, show route between them
        if (markers.length == 2) {
            showRouteFromSelectedPoints(markers[0].getPosition(), markers[1].getPosition());
        }
    } else {
        // If in Info Mode, show info about the selected location
        if (infoMarker) {
            infoMarker.setMap(null);
        }
        infoMarker = new google.maps.Marker({
            position: location,
            map: map
        });

        // Use the geocoder to get address and place details
        geocoder.geocode({ 'location': location }, function(results, status) {
            if (status === 'OK') {
                if (results[0]) {
                    var placeId = results[0].place_id;

                    var detailsRequest = {
                        placeId: placeId
                    };
                    placesService.getDetails(detailsRequest, function(place, status) {
                        if (status == google.maps.places.PlacesServiceStatus.OK) {
                            var content = `<strong>${place.name || ''}</strong><br>
                                        ${place.formatted_address}<br>`;
                            if (place.photos && place.photos.length > 0) {
                                content += `<img src="${place.photos[0].getUrl({maxWidth: 200, maxHeight: 200})}" alt="${place.name || 'Location'}">`;
                            }
                        // Display Reviews
                        // if (place.reviews && place.reviews.length > 0) {
                        //     content += `<br><br><strong>Reviews:</strong><br>`;
                        //     for (let review of place.reviews) {
                        //         content += `"${review.text}" - ${review.author_name}<br>`;
                        //     }
                        // }
                            var infoWindow = new google.maps.InfoWindow({
                                content: content,
                                position: location,
                            });
                            infoWindow.open(map, infoMarker);
                        } else {
                            var infoWindow = new google.maps.InfoWindow({
                                content: results[0].formatted_address,
                                position: location,
                            });
                            infoWindow.open(map, infoMarker);
                        }
                    });
                } else {
                    alert('No results found');
                }
            } else {
                alert('Geocoder failed due to: ' + status);
            }
        });
    }
}

// Display routes from two selected points on the map
function showRouteFromSelectedPoints(start, end) {
    getEstimatedTimeAndRoute(start, end, 'DRIVING', drivingDirectionsRenderer, "Driving", "blue");
    getEstimatedTimeAndRoute(start, end, 'WALKING', walkingDirectionsRenderer, "Walking", "green");
    getEstimatedTimeAndRoute(start, end, 'BICYCLING', bicyclingDirectionsRenderer, "Bicycling", "red");
}

// Use inputs to navigate between two addresses
function navigate() {
    var start = document.getElementById("startInput").value;
    var end = document.getElementById("endInput").value;

    getEstimatedTimeAndRoute(start, end, 'DRIVING', drivingDirectionsRenderer, "Driving", "blue");
    getEstimatedTimeAndRoute(start, end, 'WALKING', walkingDirectionsRenderer, "Walking", "green");
    getEstimatedTimeAndRoute(start, end, 'BICYCLING', bicyclingDirectionsRenderer, "Bicycling", "red");
}

// Fetch estimated time and route for a specific mode of transportation
function getEstimatedTimeAndRoute(start, end, mode, renderer, modeText, color) {
    // Define the request object with route details
    var request = {
        origin: start,
        destination: end,
        travelMode: mode
    };

    // Use the directionsService to get the route
    directionsService.route(request, function(result, status) {
        // If the route is successfully fetched
        if (status == 'OK') {
            // Display the route on the map
            renderer.setDirections(result);

            // Extract the duration of the route
            var duration = result.routes[0].legs[0].duration.text;

            // Calculate the midpoint of the route for placing the InfoWindow
            var midPoint = result.routes[0].legs[0].steps[Math.floor(result.routes[0].legs[0].steps.length / 2)].start_location;

            // Check if an InfoWindow already exists at this midpoint
            var existingInfoWindow = infoWindows.find(iw => iw.getPosition().equals(midPoint));

            // If an InfoWindow already exists, append the new duration information
            if (existingInfoWindow) {
                existingInfoWindow.setContent(existingInfoWindow.getContent() + '<br>' + `<span style="color:${color}">${modeText}: ${duration}</span>`);
            } else {
                // If no InfoWindow exists, create a new one with the duration information
                var infoWindow = new google.maps.InfoWindow({
                    content: `<span style="color:${color}">${modeText}: ${duration}</span>`,
                    position: midPoint
                });
                infoWindows.push(infoWindow);
                infoWindow.open(map);
            }
        } else {
            // Alert the user if there was an issue fetching the route
            alert('Navigation was not successful for the following reason: ' + status);
        }
    });
}