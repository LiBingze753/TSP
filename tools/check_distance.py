import math, random, re
def parse(p):
    txt=open(p).read().splitlines()
    n=int([l for l in txt if l.upper().startswith("DIMENSION")][0].split(":")[1])
    i=[k for k,l in enumerate(txt) if l.upper().startswith("NODE_COORD_SECTION")][0]
    pts=[]
    for l in txt[i+1:]:
        if l.strip().upper().startswith("EOF") or not l.strip(): break
        a=l.split(); pts.append((float(a[1]),float(a[2])))
    return n,pts
def dist(pts):
    n=len(pts); d=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i!=j:
                d[i][j]=int(math.floor(math.hypot(pts[i][0]-pts[j][0],pts[i][1]-pts[j][1])+0.5))
    return d
def length(t,d):
    n=len(t); return sum(d[t[i]][t[(i+1)%n]] for i in range(n))
def two_opt(t,d):
    n=len(t); improved=True
    while improved:
        improved=False
        for i in range(n-1):
            for j in range(i+2,n):
                if i==0 and j==n-1: continue
                a,b=t[i],t[(i+1)%n]; c,e=t[j],t[(j+1)%n]
                delta=d[a][c]+d[b][e]-d[a][b]-d[c][e]
                if delta<0:
                    t[i+1:j+1]=reversed(t[i+1:j+1]); improved=True
    return t
random.seed(7)
for name in ["eil51","berlin52","st70"]:
    n,pts=parse(f"data/{name}.tsp"); d=dist(pts)
    best=10**9
    for r in range(30):
        t=list(range(n)); random.shuffle(t)
        t=two_opt(t,d); L=length(t,d)
        if L<best: best=L
    print(name, "n=",n, "best 2-opt over 30 restarts =", best)
