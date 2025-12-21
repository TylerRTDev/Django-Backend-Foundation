Document.addEventListener("click", async (e) => {
    const link = e.target.closest("a[data-spa-link]");
    if (!link) return;

    e.preventDefault();
    const url = link.href;

    const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const html = await response.text();

    // Expect the server to send only the inner HTML for content
    document.querySelector("#page-content").innerHTML = html;
    window.history.pushState({}, "", url);
});