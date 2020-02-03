# %% 
import pymc3 as pm 
import numpy as np 
import scipy.stats as stat 
import matplotlib.pyplot as plt 
import arviz as az 

az.style.use('arviz-darkgrid')

# %%
dummy_data = np.loadtxt('/home/brown5628/projects/bayesian-data-analysis/data/dummy.csv')
x_1 = dummy_data[:,0]
y_1 = dummy_data[:,1]

order = 2
x_1p = np.vstack([x_1**i for i in range(1, order+1)])
x_1s = (x_1p - x_1p.mean(axis=1, keepdims=True)) / x_1p.std(axis=1, keepdims=True)
y_1s = (y_1 - y_1.mean()) / y_1.std()
plt.scatter(x_1s[0], y_1s)
plt.xlabel('x')
plt.ylabel('y')

# %%
with pm.Model() as model_1:
    alpha = pm.Normal('alpha', mu=0, sd=1)
    beta = pm.Normal('beta', mu=0, sd=10)
    error = pm.HalfNormal('error', 5)

    mu = alpha + beta * x_1s[0]

    y_pred = pm.Normal('y_pred', mu=mu, sd=error, observed=y_1s)

    trace_1 = pm.sample(2000)

# %%
with pm.Model() as model_p:
    alpha = pm.Normal('alpha', mu=0, sd=1)
    beta = pm.Normal('beta', mu=0, sd=10, shape=order)
    error = pm.HalfNormal('error', 5)

    mu = alpha + pm.math.dot(beta, x_1s)

    y_pred = pm.Normal('y_pred', mu=mu, sd=error, observed=y_1s)

    trace_p = pm.sample(2000)

# %%
x_new = np.linspace(x_1s[0].min(), x_1s[0].max(), 100)

alpha_1_post = trace_1['alpha'].mean()
beta_1_post = trace_1['beta'].mean(axis=0)
y_1_post = alpha_1_post + beta_1_post * x_new 

plt.plot(x_new, y_1_post, 'C1', label='linear model')

alpha_p_post = trace_p['alpha'].mean()
beta_p_post = trace_p['beta'].mean(axis=0)
idx = np.argsort(x_1s[0])
y_p_post = alpha_p_post + np.dot(beta_p_post, x_1s)

plt.plot(x_1s[0][idx], y_p_post[idx], 'C2', label=f'model order {order}')

alpha_p_post = trace_p['alpha'].mean() 
beta_p_post = trace_p['beta'].mean(axis=0)
x_new_p = np.vstack([x_new**i for i in range(1, order+1)])
y_p_post = alpha_p_post + np.dot(beta_p_post, x_new_p)

plt.scatter(x_1s[0], y_1s, c='C0', marker='.')
plt.legend()
plt.show()

# %%
y_1 = pm.sample_posterior_predictive(trace_1, 200, model=model_1)['y_pred']
y_p = pm.sample_posterior_predictive(trace_p, 2000, model=model_p)['y_pred']

# %%
plt.figure(figsize=(8,3))
data = [y_1s, y_1, y_p]
labels = ['data', 'linear model', 'order 2']
for i, d in enumerate(data):
    mean = d.mean()
    err = np.percentile(d, [25,75])
    plt.errorbar(mean, -i, xerr=[[-err[0]], [err[1]]], fmt='o')
    plt.text(mean, -i+.2, labels[i], ha='center', fontsize=14)
plt.ylim([-i-.5, .5])
plt.yticks([])

# %%
fig, ax = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)


def iqr(x, a=0):
    return np.subtract(*np.percentile(x, [75, 25], axis=a))


for idx, func in enumerate([np.mean, iqr]):
    T_obs = func(y_1s)
    ax[idx].axvline(T_obs, 0, 1, color='k', ls='--')
    for d_sim, c in zip([y_1, y_p], ['C1', 'C2']):
        T_sim = func(d_sim, 1)
        p_value = np.mean(T_sim >= T_obs)
        az.plot_kde(T_sim, plot_kwargs={'color': c},
                    label=f'p-value {p_value:.2f}', ax=ax[idx])
    ax[idx].set_title(func.__name__)
    ax[idx].set_yticks([])
    ax[idx].legend()
    plt.show()

# %%
x = np.array([4.,5.,6.,9.,12,14.])
y = np.array([4.2, 6., 6., 9., 10, 10.])

plt.figure(figsize=(10,5))
order = [0,1,2,5]
plt.plot(x, y, 'o')
for i in order:
    x_n = np.linspace(x.min(), x.max(), 100)
    coeffs = np.polyfit(x, y, deg=i)
    ffit = np.polyval(coeffs, x_n)

    p =np.poly1d(coeffs)
    yhat = p(x)
    ybar = np.mean(y)
    ssreg = np.sum((yhat-ybar)**2)
    sstot = np.sum((y - ybar)**2)
    r2 = ssreg / sstot 

    plt.plot(x_n, ffit, label=f'order {i}, $R^2$= {r2:.2f}')

plt.legend(loc=2)
plt.xlabel('x')
plt.ylabel('y', rotation=0)

# %%
waic_1 = az.waic(trace_1)
waic_1
# %%
cmp_df = az.compare({'model_1':trace_1,'model_p':trace_p}, method='BB-pseudo-BMA')
cmp_df

# %%
az.plot_compare(cmp_df)

# %%
w = .5
y_lp = pm.sample_posterior_predictive_w([trace_1, trace_p], samples=1000, models=[model_1, model_p], weights=[w, 1-w])

_, ax = plt.subplots(figsize=(10,6))
az.plot_kde(y_1, plot_kwargs={'color':'C1'}, label='linear model', ax=ax)
az.plot_kde(y_p, plot_kwargs={'color':'C2'}, label='order 2 model', ax=ax)
az.plot_kde(y_lp['y_pred'], plot_kwargs={'color':'C3'}, label='weighted model', ax=ax)

plt.plot(y_1s, np.zeroes_like(y_1s), '|', label='observed data')

plt.y_ticks([])
plt.legend()
plt.show()

# %%
coins = 30
heads = 9
y_d = np.repeat([0,1], [coins-heads, heads])



# %%
with pm.Model() as model_bf:
    p = np.array([.5, .5])
    model_index = pm.Categorical('model_index', p=p)

    m_0 = (4,8)
    m_1 = (8,4)
    m = pm.math.switch(pm.math.eq(model_index,0), m_0, m_1)

    theta = pm.Beta('theta', m[0], m[1])

    y = pm.Bernoulli('y', theta, observed=y_d)

    trace_bf = pm.sample(5000)

az.plot_trace(trace_bf)

# %%
pm1 = trace_bf['model_index'].mean()
pm0 = 1 - pm1 
bf = (pm0 / pm1) * (p[1] / p[0])

# %%
bf

# %%
with pm.Model() as model_bf_0:
    theta = pm.Beta('theta', 4, 8)
    y = pm.Bernoulli('y', theta, observed = y_d)
    trace_bf_0 = pm.sample(2500, step=pm.SMC())

with pm.Model() as model_bf_1:
    theta = pm.Beta('theta', 8, 4)
    y = pm.Bernoulli('y', theta, observed=y_d)
    trace_bf_1 = pm.sample(2500, step=pm.SMC())

model_bf_0.marginal_likelihood / model_bf_1.marginal_likelihood

# %%
traces = []
waics = []
for coins, heads in [(30, 9), (300, 90)]:
    y_d = np.repeat([0,1], [coins-heads, heads])
    for priors in [(4,8), (8,4)]:
        with pm.Model() as model:
            theta = pm.Beta('theta', *priors)
            y = pm.Bernoulli('y', theta, observed=y_d)
            trace = pm.sample(2000)
            traces.append(trace)
            waics.append(az.waic(trace))
plt.show()
# %%
#fig, ax = plt.subplots(1,2, sharey=True)

#labels = model_names
#indices = [0, 0, 1, 1]
#for i, (ind, d) in enumerate(zip(indices, waics)):
#    mean = d.waic 
#    ax[ind].errorbar(mean, -i, xerr=d.waic_se, fmt='o')
#    ax[ind].text(mean, -i+.2, labels[i], ha='center')

#ax[0].set_xlim(30, 50)
#ax[1].set_xlim(330, 400)
#plt.ylim([-i-.5, .5])
#plt.yticks([])
#plt.subplots_adjust(wspace=.5)
#fig.text(.5, 0, 'Deviance', ha='center', fontsize=14)
#plt.show()

# %%
np.random.seed(912)
x = range(0, 10)
q = stat.binom(10, .75)
r = stat.randint(0, 10)

true_distribution = [list(q.rvs(200)).count(i) / 200 for i in x]

q_pmf = q.pmf(x)
r_pmf = r.pmf(x)

_, ax = plt.subplots(1, 3, figsize=(12,4), sharey=True, constrained_layout=True)

for idx, (dist, label) in enumerate(zip([true_distribution, q_pmf, r_pmf], ['true_distribution', 'q', 'r'])):
    ax[idx].vlines(x, 0, dist, label=f'entropy = {stat.entropy(dist):.2f}')
    ax[idx].set_title(label)
    ax[idx].set_xticks(x)
    ax[idx].legend(loc=2, handlelength=0)

# %%
