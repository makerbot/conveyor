The internals of the process module are structured like a lambda calculus
evaluator (although without closures, Abs, and App). The rationale is:

1. We already need something isomorphic to evaluation contexts to track
   progress through a process. We might as well model and use evaluation
   contexts directly.

   An evaluation context is similar to a stack frame in that it stores the
   current location where a program is evaluating. It represents a "hole" in a
   program into which a value will be produced once a subterm has been
   evaluated.

   Most contexts have an enclosing context. These form a chain that is similar
   to how a collection of stack frames form a call stack. The abort context
   (_ContextAbort) is special in that it has no enclosing context.

   Consider this short example of evaluating a binary operator in an
   environment where "x" is "1" and "y" is "2":

        x + y
        ------
        [] + y
        ------
        1 + []
        ------
        1 + 2
        ------
        3

   Here '[]' represents the context or hole. Note that there are two contexts
   for the "+" term: one where the hole is to the left of the operator and one
   where the hole is to the right. There is a distinct context type for each
   place where a term has a subterm. A binary operator has two subterms and
   therefore two evaluation contexts. A unary operator has a single subterm and
   therefore a single context. A literal term has no subterms and therefore no
   contexts. (Note that we do not actually support binary operators nor unary
   operators.)

   In our system, evaluation contexts track progress through a sequence of
   tasks.

        task1 task2 task3
        -----------------------
        [] task2 task3
        -----------------------
        result1 [] task3
        -----------------------
        result1 result2 []
        -----------------------
        result1 result2 result3

2. In the future we might want to add control structures. This implementation
   provides a good foundation upon which they can be built (and note that
   there is currently *zero* code to support this future possibility).

3. It's well-known and less complicated than this description may lead you to
   believe.

It is a refocusing evaluator because the complexity of a refocusing evaluator
is at worst the same as that of a traditional decompose/plug evaluator. It is
usually better.

It is structured as a state machine. Here states are called "phases" in order
to avoid a terminology conflict with the world state that is threaded through
the evaluator.

Traditionally a refocusing interpreter has two states: refocus and
refocus_aux. This implementation adds states for abort and yield.

1. _PhaseAbort
2. _PhaseRefocus
3. _PhaseRefocusAux
4. _PhaseYield

The state machine implementation is trampolined because:

1. Python is not tail recursive (!&#!**!@).

2. We need to suspend the machine while evaluating a yield term. Yield simply
   stores the current thunk (_PhaseYield) and exits the trampoline loop.

   Threads might work, but this implementation is less complex than threads.
   Threads would also preclude us from storing a partially evaluated process
   on disk and resuming it in a subsequent execution of conveyor (i.e., with
   this design we can resume a process even if your computer crashes).

3. It is almost always a mistake to tie an evaluator to the host language's
   call stack. Here it is even more of a mistake because we need to suspend
   the machine while evaluating a yield term.

The environment represents information that is passed top-down through the
tree of terms. Values represent information that is passed bottom-up through
the tree of terms. The world state represents information that is passed
through the term tree in evaluation order (which is defined as left-to-right
for this machine).

The environment and state (and frequently the values) are threaded through
the evaluator even though they are unused. It's cheap to do now and much
harder to retrofit later (and, from personal experience, each time I have
omitted them from an evaluator I had to go back and add them.) This is the
only unused code in the implementation.

See:

  * Refocusing in Reduction Semantics  
    <http://www.brics.dk/RS/04/26/BRICS-RS-04-26.pdf>
