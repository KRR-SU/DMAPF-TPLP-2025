#program path_constraints(t,k). 
#external path_query(t,k). % rescheduling of the plan starts at time k

% every two consecutive and different vertex pair in the plan forms a plan pair
plan_pair(A,X,Y,t,k) :- plan(A,T-1,X), plan(A,T,Y), X!=Y, edge(X,Y), old_agent(A), path_query(t,k). 
% number of occurrences of each pair in the plan are counted
plan_pair_count(A,X,Y,C1,t,k):- C1 = #count{X,Y,T: plan(A,T-1,X), plan(A,T,Y), X!=Y}, plan_pair(A,X,Y,t,k), old_agent(A), path_query(t,k).

% the number of occurrences of a pair in the plan and the number of occurrences of a pair in the path should be the same
:- plan_pair_count(A,X,Y,C1,t,k), path_pair_count(A,X,Y,C), C1!=C, old_agent(A), path_query(t,k).

% every vertex appearing in the plan should also appear in the path
:- plan(A,_,X), not path(A,X), old_agent(A), path_query(t,k). 
% every vertex appearing in the path should also appear in the plan
:- not plan(A,_,X), path(A,X), old_agent(A), path_query(t,k).

