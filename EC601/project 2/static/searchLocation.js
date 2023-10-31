// Function to search for a location and update the map to center on that location
function searchLocation() {
    // Create a new geocoder object from the Google Maps API
    var geocoder = new google.maps.Geocoder();
    
    // Get the value entered in the address input field by the user
    var address = document.getElementById("addressInput").value;

    // Use the geocoder to convert the address into latitude and longitude
    geocoder.geocode({'address': address}, function(results, status) {
        // Check if the geocode request was successful
        if (status === 'OK') {
            // Update the map's center to the geocoded location
            map.setCenter(results[0].geometry.location);
            
            // Set the map's zoom level to 15
            map.setZoom(15);
        } else {
            // If the geocode request was unsuccessful, show an alert with the error message
            alert('Search was not successful for the following reason: ' + status);
        }
    });
}
