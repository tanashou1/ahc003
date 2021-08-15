import create_instance
import step
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
import pymc3 as pm    


def linear(ct_list, sum_list, ans, ridge=1.):
    x = np.array(ct_list)
    y = np.array(sum_list)

    if ridge > 0:
        reg = Ridge(alpha=1).fit(x, y)
    else:
        reg = LinearRegression().fit(x, y)

    err = sum([min(a, abs(v - a))/a for v, a in zip(reg.coef_, ans)]) / len(ans)
    accuracy = 1. - err

    return reg.coef_, accuracy


def linear_with_line(ct_list, sum_list, ans, h, v, ridge=1.):
    ct_list_with_line = [step.convert_ct_with_line(ct, h, v) for ct in ct_list]

    coefs, _ = linear(ct_list_with_line, sum_list, ans, ridge)

    res = step.convert_without_line(coefs, h, v)

    err = sum([min(a, abs(v - a))/a for v, a in zip(res, ans)]) / len(ans)
    accuracy = 1. - err

    return res, accuracy


def dot(x_list, ct_list):
    in_list = []
    ct = np.array(ct_list).T

    for i, x in enumerate(x_list):
        in_list.append(x * ct[i])
    
    return sum(in_list)


def xdot(X, ct_list):
    in_list = []
    ct = np.array(ct_list).T

    for i in range(len(ct[0])):
        in_list.append(X[i] * ct[i])
    
    return sum(in_list)


def bayesian(ct_list, sum_list, ans):
    y = np.array(sum_list)
    # モデル
    with pm.Model() as model:
        # 1. 事前分布
        x_list = []
        for i, _ in enumerate(ct_list[0]):
            x = pm.Normal(f"x{i}", mu=5000., sd=10000.)
            # x = pm.Uniform(f"x{i}", lower=1000, upper=10000, testval=5000)
            x_list.append(x)
        # x_list = pm.Normal(f"x", mu=5000, sd=5000, shape=len(ct_list[0]))
        
        epsilon = pm.HalfNormal('epcilon', sd=10000)
        # 2. 尤度の計算
        m = dot(x_list, ct_list)
        print(m)
        y_pred = pm.Normal('y_pred', mu=m, sd=epsilon, observed=y)
        # 3. MCMCの実行
        trace = pm.sample(6000, chains=1)
    
    trace_n = trace[1000:]

    coefs = []
    for i, _ in enumerate(ans):
        coefs.append(trace_n[f"x{i}"].mean())

    err = sum([min(a, abs(v - a))/a for v, a in zip(coefs, ans)]) / len(ans)
    accuracy = 1. - err

    return coefs, accuracy
