# Stuart
_a [GDD](https://pirate.baby/posts/generative_driven_design/) experiment_


>[!WARNING]
> This code doesn't do much of anything yet. The meat, at the moment, is in discussion of the concept as stated here.👇

## The Problem
When generating code with an LLM, size matters. Consider the most impressive examples of genAI coding: simple greenfield scripts and tiny, atomic application changes (like updating a button or fixing a bug) that require an inerently limited context. That is why they work so well. But once the reference code grows in size and spreads across multiple modules, generations quickly degrade; context volume waters down what should ideally be precision completions, and you get compounding halucinations, loopy, rambling code, and eventual breakdown. These generations also add cruft that would make sense in the context of a stand-alone script, but clog the codebase of full-blown application - in turn making subsequent generations worse and compounding the issue.

Unlike chatbot RAG, the effectiveness of codebase RAG is limited - semantic similarity does much more for natural lanaguage than for code prediction. Novel RAG techniques involving AST parsing have made things a little better, but there's a notable cliff in the size of the application this works for.

## The Theory

### Why code looks the way it does
At the lowest level, binary programming is a series of switch states (on and off). Early computer users needed a repeatable way to author and execute those states, so we punched holes in paper cards to represent these instructions or "programs". Subsequent layers of abstraction represented these instructions in human written languages, but that didn't _have_ to be the case - we could have programmed in something that resembled sheet music or cartography, however we chose our human written languages. We added design paradigms to these langauages, like Object Oriented Programming, to give our code increasingly familiar real-world analogs - "`Dog` inherits from `Animal`, `Beagle` inherits from `Dog`" and "this file belongs in this folder under this subfolder." These constructs are useful to **humans** because we can easily pattern match with those real-world analogs, and they match how we think. This system of cues and analogs is actually very complex, and it is only because it closely mirrors human thinking and memory that it is preferable to a very different code structure.

### LLM coding size and context
What do we know about LLM code completions (most specifically in regard to instruct models)? We know that training pairs trend towards highly focused code "snippets." Consider the format in Stack Overflow, GitHub issues, and similar sources of code training: a user posts redacted bits of code that are deemed relevant, then asks a question, and responses are similarly formatted. It is no surprise that code snippets are where these models excel; "write some Python to get the current weather for next week" and "write an image carousel in JavaScript" are isolated, atomic and targeted code blurbs that require minimal context traversal.

We also know that poor context stuffing severely impairs generation quality. Dump the whole of a tiny application into the system prompt as context, and even simple requests turn to slush. RAG can help mitigate this degradation effect at a toy scale, but even very small projects lose fidelity to the point of failure very quickly. Case in point: When the `CONTRIBUTING.md` file in this repository was added to the Copilot working set, proceeding completions followed the instructions to check for non-code solutions and always start with tests. As the working set grew by just a few files, completions began ignoring those instructions even when directly prompted - the noise from oversaturated RAG washed out the prompts.

### The rub
Herein lies the problem: humans rely heavily on context constructs - our cues and analogs - to code efficiently. LLMs struggle with context constructs, but excel when working on isolated snippets. So this means that the software we write today using human "best practices" is woefully unsuited for the strengths of generative AI coding.

### Writing code for LLMs
LLMs are much, much faster than humans, and can process information in an infinitely parallel pattern. Imagine that a human mind could find [every instance of the word "parallel" in the Django codebase](https://github.com/search?q=repo%3Adjango%2Fdjango%20parallel&type=code) in _under 600ms_. Would we have bothered creating lexical structures like classes and modules? Or would Django be one large file?

Instead of storing code in document-like corpuses and searching them like prose, instead of requiring mounds of context to modify functionality, what if we architect our codebase as a flat, construct-less collection of atomic, stateless, "snippet-friendly" functions, and built our code generation steps as assembling series of isolated snippet prompts.

> [!NOTE]
> Yes, this sounds a lot like functional programming. And the takeaway could be that 'functional programming is better suited for LLMs than OOP', but I don't believe it is that simple. I'm intentionally avoiding FP here because while the mechanics are similar, the goals are very different. FP is a human design philosophy with human programmer goals, where this Generative Driven Design pattern is intended to put LLM developers' needs first.

To an LLM, Python is an extremely efficient store of information - "open the file 'file.txt' as bytes" takes fewer tokens in Python than in English or in C. It makes sense to build these snippets in languages that are efficient and have massive volumes of training data readily available. But it is important to distinguish that additional constraints on the language must be in place to make sure snippet code is optimized for LLM completions. For example, `pytest` heavily leverages global `fixtures` defined in `conftest.py`, creating "magic" dependency injections in test modules that require contextual understanding of the project; this may be a Python best practice, but it is detrimental to our needs in _GDD_. It may actually be best for agent processes to build test functions without the `pytest` framework, instead creating atomic snippets to check functionality. Point being that the stored programming language - ideally Python or JavaScript based on the coding models available today - is a vessel for this generative-first development paradigm, not a superset of the process.

### Implementation
In this repo I'm attempting a proof of a "snippet assembly" codebase. Code elements are stored in sqlite with varying granularity:
  - highest level topography tree: modules, submodules and methods (names only)
  - module details: names, descriptions, imports
  - typing details: names, uses
  - function details: names, arity, relationships between functions, schemas and constants
  - function bodies: the code of the function
  - schema bodies: the code of the schema

Work is (at least initially) assigned by a cli `ask` command. (Yes, this could eventually be triggered by GitHub issues or a Slackbot etc etc).

The agent process modifies the codebase through function calling, adding/updating/removing functions, modules, types, and constants through calls.
Processes will follow a pipeline that has a rough pattern of:
1. review the human ask and plan the task without any code context, but with a strict pattern instruction set (sanity check if ask is possible, TDD, etc)
2. iterate through planned tasks to build out topography in context, with function calls to select elements for each generation context
  a. with each generation, function calls update the modules/functions etc in sqlite and then the entire codebase is re-rendered.
  b. the impacted tests are run, failing tests are passed back in context to another generation, code is updated - this loop is recursive (with some kind of safety bubble-up to a supervisor process)
  c. full-codebase regression tests are run, recursion as above
3. refactoring is top-down and minimal, because things like formatting and linting aren't appropriate. Linting and formatting are human helpers.
3. the db state is committed with details, and the rendered codebase is committed as a _read only artifact_ purely for human review.

> [!TIP]
> Code is rendered in the repo as an artifact only for the benefit of the humans. Similar to compiled JS or the rendered HTML in an SPA, this is read-only and you need to modify the source (in this case the db binary) to modify the code.

We'll need some way to make human mods to code - maybe a `editable <function_name>` cli command that renders the code in a .py file, then parses it back into the db on save? Ideally this shouldn't be the norm; once we start rendering the whole codebase all the time, humans will want to apply those constructs to make life easier for humans (and subsequently harder for the LLM), and we will slide backwards.

### What next?
**The code in this repo does almost nothing at the moment. So, there's that.**
First up is completing the elements described above so they actually do what is described, and developing the a first GDD codebase for a simple app to prove viability of the approach. Then seeing if there is evidence that it can work. Especially:
- does it work over many iterations? Do we avoid "bot rot" or is that still an eventuality of LLM code?
- how does growing codebase complexity impact effectiveness?
- what do humans need to "step in" for? can we capture and codify these processes too?


<details>
<summary>Why Stuart?</summary>
<img alt="Stuart from MadTV" src="https://media0.giphy.com/media/czZlH3xg1Ul2w/giphy.gif?cid=6c09b952811227g3c0p6f02kcndisopi0z8019a9a9kab7h6&ep=v1_gifs_search&rid=giphy.gif&ct=g"/>

This is what every AI coding agent feels like to me at some level.
</details>
