//@ts-ignore
import { marked } from 'marked';


const renderer = {
    //@ts-ignore
link({ href, title, text }) {
    const localLink = href.startsWith(
    `${location.protocol}//${location.hostname}`
    );

    // to avoid title="null"
    if (title === null) {
    return localLink
        ? `<a href="${href}">${text}</a>`
        : `<a target="_blank" rel="noreferrer noopener" href="${href}">${text}</a>`;
    }
    return localLink
    ? `<a href="${href}" title="${title}">${text}</a>`
    : `<a target="_blank" rel="noreferrer noopener" href="${href}" title="${title}">${text}</a>`;
},
};

//@ts-ignore
marked.use({ renderer });


export default marked