document.addEventListener("DOMContentLoaded", () => {
    const eventoSelect = document.getElementById("evento");
    const mensaje = document.getElementById("mensaje");

    // Cargar eventos disponibles
    fetch("/eventos-disponibles")
        .then(res => res.json())
        .then(data => {
            data.forEach(evento => {
                const opcion = document.createElement("option");
                opcion.value = evento.id;
                opcion.textContent = `${evento.titulo} (${evento.fecha})`;
                eventoSelect.appendChild(opcion);
            });
        });

    // Enviar formulario
    const form = document.getElementById("reservaForm");
    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const datos = {
            nombre: form.nombre.value,
            email: form.email.value,
            cupos: parseInt(form.cupos.value),
            evento_id: parseInt(form.evento.value),
        };

        fetch("/reservas", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        })
        .then(res => res.json().then(data => ({ status: res.status, body: data })))
        .then(({ status, body }) => {
            if (status >= 200 && status < 300) {
                mensaje.textContent = "¡Reserva realizada con éxito!";
                mensaje.style.color = "green";
                form.reset();
            } else {
                mensaje.textContent = body.detail || "Error al reservar.";
                mensaje.style.color = "red";
            }
        })
        .catch(() => {
            mensaje.textContent = "Error de conexión con el servidor.";
            mensaje.style.color = "red";
        });
    });
});