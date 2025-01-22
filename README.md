# Stuart
_a GDD experiment_
![Stuart from MadTV](https://media0.giphy.com/media/czZlH3xg1Ul2w/giphy.gif?cid=6c09b952811227g3c0p6f02kcndisopi0z8019a9a9kab7h6&ep=v1_gifs_search&rid=giphy.gif&ct=g)


## The Problem
When generating code with an LLM, size matters. Consider the most impressive examples of genAI coding: simple greenfield scripts and tiny, atomic application changes (like updating a button or fixing a bug) that require an inerently limited context. That is why they work so well. But once the reference code grows in size and spreads across multiple modules, generations quickly degrade; context volume waters down what should ideally be precision completions. These generations add cruft that would make sense in the context of a stand-alone script, but clog the codebase of full-blown application.

Unlike chatbot `RAG`, the effectiveness of codebase `RAG` is limited - semantic similarity does much more for natural lanaguage than for code. And meaningful architectural refactoring at this scale is impossible.

## The Theory

instead of storing code in document-like corpuses and soft-searching them like text, context is built for each ask with the needed granularity - several levels are stored:
  - highest level topology tree: modules, submodules and methods (names only)
  - module details: names, descriptions, imoports
  - schema details: names, uses
  - function details: names, arity, relationships
  - function bodies: the code
  - schema bodies: the code

The process traverses up and down the "spine" of the codebase and assembles appropreate context, made possible by the relationship mapping stored with the components.

All code is atomic, functional, and stateless - allowing the assembled code and modified code to be "snippet-like" (exactly what LLMs excel at!).

Code elements - modules, functions, constants - are created and modified via function calls that restrict the generation of cruft. The codebase is then compiled at rendering, but it is only an artifcact.

Refactoring has distinct, natural entrypoints thanks to the functional design and the different granularities. For example, a review of the top tree can identify duplicate function business logic. The functional (stateless, dependency injection) nature of the code, combined with the referential associations between functions, allows for schema and arity changes to be naturally DRY.

Tests are just functions in the `test` module, and operate the same as the rest of the codebase.




