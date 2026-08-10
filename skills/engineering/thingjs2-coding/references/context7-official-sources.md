# Context7 official ThingJS sources

Use this reference when the task needs Context7 retrieval. Context7 is already
configured for this workspace, and these two allowlisted libraries are the
user-approved mirrors of the official ThingJS 2.0 corpus:

| Context7 library ID | Original source | Current retrieval quality | Safe default |
| --- | --- | --- | --- |
| `/websites/thingjs_new` | `https://docs.thingjs.com/new/documentation/` | High reputation, sparse coverage (8 snippets) | Use for ThingJS 2.0 concepts and page discovery; fall back for exact signatures |
| `/websites/cdn_uino_cn_thingjs_apidocs` | `https://cdn.uino.cn/thingjs/APIdocs/` | First-party CDN corpus, low retrieval quality (316 snippets) | Use only after owner/member/provenance checks; wrong-owner and private-page hits are known |

## Trust model

The Context7 MCP transport can be trusted for these two approved official
corpora. A returned snippet may carry the `official_verified` evidence label only
when all of the following are true:

1. The library ID is one of the two allowlisted IDs above.
2. The result preserves an exact first-party `Source:` URL.
3. The result names the requested public owner and member, with the exact
   signature or behavior needed by the task.
4. The page is a public API/documentation page, not a source implementation,
   private member, generated internals page, or compatibility page.
5. The result is in ThingJS 2.0 scope and contains no 1.x, compatibility, or
   `t3d` pollution.

This is provenance-gated trust, not blind acceptance of every search hit. The
Context7 channel does not make a wrong-owner snippet correct. Preserve the
Context7 library ID, original URL, query, retrieval time, and evidence label in
the local API Cache record.

## Known rejection cases

- Block `/uinosoft/t3d.js` even though Context7 may rank it highly.
- Block `thing_src_*` implementation pages and private/internal members.
- Reject a `THING.App.load` query that returns `BlueprintComponent.load` or a
  resource-internal `BaseResource` method.
- Reject a result that only describes the platform generally when an exact API
  signature is required.
- Reject compatibility material such as the `28_compatible` documentation page.

When any rejection condition applies, use the exact official API or
documentation page directly and keep the Context7 result as a retrieval
incident. Do not silently substitute a similarly named method.

## Query templates

Use focused, owner-qualified queries:

```text
THING.App constructor and THING.App.load(url, options), public API only
THING.Entity constructor, onComplete, and waitForComplete, public API only
THING.BaseObject on/off/once with owner, condition, callback, and tag
THING.BaseObject.destroy return value and lifecycle behavior
```

Run one topic at a time. If a result does not preserve the owner and source
page, stop using it and perform the official-web fallback.
