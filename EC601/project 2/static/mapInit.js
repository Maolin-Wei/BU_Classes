// Declare a global variable for the map object.
var map;

// Define a function to initialize the map.
function myMap() {
    // Create a new geocoder object from the Google Maps API.
    var geocoder = new google.maps.Geocoder();

    // Define the address to be geocoded.
    var address = "Boston University";

    // Use the geocoder to convert the address into latitude and longitude.
    geocoder.geocode({'address': address}, function(results, status) {
        // Check if the geocode request was successful.
        if (status === 'OK') {
            // Define properties for the map.
            var mapProp= {
                // Set the center of the map to the geocoded location.
                center: results[0].geometry.location,
                // Set the initial zoom level.
                zoom: 15,
                // Ensure that icons on the map aren't clickable.
                clickableIcons: false,
            };
            
            // Initialize the map and set it to the specified DOM element with ID "googleMap".
            map = new google.maps.Map(document.getElementById("googleMap"), mapProp);
            
            // Call a function to initialize any navigation features (this function hasn't been provided in your code).
            initNavigation();
        } else {
            // If the geocode request was unsuccessful, show an alert with the error message.
            alert('Geocode was not successful for the following reason: ' + status);
        }
    });
}
