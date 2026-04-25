#program newAgent(a,i,g,k).
agent(a).
init(a,i).
goal(a,g).
agent_added(a,k).

plan(a,k,X) :- init(a,X), agent(a).

{plan(a,T,X)}1 :- plan(a,T-1,X), agent(a), time(T), T >= k.
{plan(a,T,Y): edge(X,Y)}1 :- plan(a,T-1,X), agent(a), time(T), T >= k.

:- {plan(a,T,X): vertex(X)}0, agent(a), time(T), T >= k.
:- 2{plan(a,T,X): vertex(X)}, agent(a), time(T), T >= k.

% no two agents are at the same vertex at time T.
:- 2{plan(A,T,X): agent(A)}, vertex(X), time(T), T >= k. 

% no swapping
plan_to(X,Y,T,-1) :- plan(a,T-1,X), plan(a,T,Y), edge(X,Y), agent(a), time(T), T>=k, k=0.
:- plan_to(X,Y,T,_), plan_to(Y,X,T,_), time(T), T>=k. %, plan_to_new(Y,X,T), time(T), T>=k.

goal_reached(a,T) :- goal(a,X), plan(a,T,X), agent(a), time(T), T>=k.
goal_reached(a,T) :- goal_reached(a,T-1), time(T), T>=k.

% check program for new agents at mapf makespan
:- not goal_reached(a,T), agent(a), query(T).

% make sure agent ends at goal
:- not goal(a,X), plan(a,T,X), agent(a), query(T).
