export async function apiPOST(path, body) {
    const resp = await fetch(`http://localhost:3000/api/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
}

export async function apiGET(path) {
    const resp = await fetch(`http://localhost:3000/api/${path}`, {
        method: "GET",
    });

    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
}
