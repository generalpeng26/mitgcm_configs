#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

plt.ion()

binprec = '>f4'
flag_plot = 0

Lz = 15000       # total depth
Lx = 20000     # length of the domain
Ly = 1.0       # length of the tank  (y)
gg = 9.81      # gravity
rho0z = 16.3e-4   # stratification (d rho /dz)
u0z = 1e-3     # vertical shear (du/dz) s-1
alphaK = 2.0e-4
rho0 = 1e3
nu = 1.0

# ========== grid =========

si_x = 300
si_y = 1
si_z = 400

si_x1 = si_x + 1
si_y1 = si_y + 1
si_z1 = si_z + 1

dx = Lx/si_x
dy = Ly/si_y

dx1 = dx*np.ones((si_x))
dy1 = dy*np.ones((si_y))

xx = Lx*(np.arange(0,si_x) + 0.5)/(1.0*si_x)
yy = Ly*(np.arange(0,si_y) + 0.5)/(1.0*si_y)

xx1 = Lx*(np.arange(0,si_x+1) )/(1.0*si_x)
yy1 = Ly*(np.arange(0,si_y+1) )/(1.0*si_y)

dz = Lz/si_z
dz1 = dz*np.ones((si_z))
zz = np.cumsum(dz1)

xg,yg = np.meshgrid(xx,yy) 
xu,yu = np.meshgrid(xx1[:-1],yy) 
xv,yv = np.meshgrid(xx,yy1[:-1]) 
xc,yc = np.meshgrid(xx1,yy1) 

# xf is % of grid points
xf = [0, 0.4, 0.6, 0.8, 0.9, 1]
# yf is % of thickness
yf = [0, 0.08, 0.14, 0.21, 0.4, 1]

hh = np.linspace(0,1,si_z1)
zf = Lz*np.interp(hh,xf,yf)

# smooth
nc = int(si_z/10)
if nc % 2 == 0:
  nc = nc + 1
zz2 = np.convolve(zf, np.ones((nc,))/nc, mode='valid')

zf[int((nc-1)/2):int(-(nc-1)/2)] = zz2


if flag_plot:
  plt.figure()
  plt.plot(hh,zf/Lz,'k')
  plt.plot(hh,hh,'k--')
  plt.plot(xf,yf,'.')
  plt.savefig( 'vert_res.png')
  plt.close()

dz1 = np.diff(zf)

# reverse order to get high resolution near the bottom
dz1 = dz1[::-1]
zf[1:] = np.cumsum(dz1)

iz = np.argmin(np.abs(zf-500.0))

print ('dx= ', dx)
print ('min dz: ', np.min(dz1))
print ('max dz: ', np.max(dz1))
print ('nb layers above 500m:', iz, '/', si_z)

if np.sum(dz1 < 0) > 0:
  print ('you need you change the polynomial fit!')

zc = zf[0:-1] + 0.5*dz1


dx1.astype(binprec).tofile('dx.box')
dy1.astype(binprec).tofile('dy.box')
dz1.astype(binprec).tofile('dz.box')


# ============= topography =============

h_mit = -Lz + np.zeros((si_y,si_x))

x0 = Lx/2  # m
L0 = 1000   # m
H0 = 99.5 # m not exactly 100m to avoid discretization issue 
#H0 = 99.5 # m not exactly 100m to avoid discretization issue 

h_mit = h_mit + H0*(np.exp(-(xg-x0)**2/(2*L0**2)))  #H0/(1+(xg-x0)**2/(2*L0**2))
h_mit.astype(binprec).tofile('topo.box')

# ========= initial conditions ==========

# === linear stratification
tinit = rho0z/(rho0*alphaK)*(Lz-zc.reshape((si_z,1,1))) + np.zeros((si_z,si_y,si_x));

tinit.astype(binprec).tofile('tinit.box')

tref = tinit[:,0,0]
tref.astype(binprec).tofile('tref.box')


# === initial velocity
#u_trans = 0.1

uvel = u0z*(Lz-zc.reshape((si_z,1,1))) + np.zeros((si_z,si_y,si_x));

# uniform velocity above Hu
#umask = np.zeros((si_z,si_y,si_x)) + zc.reshape(si_z,1,1)

#Hu = 5000
#uvel = np.where(umask<Lz-Hu,u0z*Hu,uvel)

uvel.astype(binprec).tofile('uinit.box')

# # === RBCS files
tmask  = np.zeros((si_z,si_y,si_x));


#bottom boundary
tmask[-1,:,:] = 1.0

# # lower boundary over the topo
# tmask2 = 0*tmask - zf[1:].reshape(si_z,1,1)
# tmask3 = np.where(tmask2<h_mit,1.0,0.0)
# tmask = tmask + tmask3
# tmask = np.where(tmask>0,1,0)


# upper sponge
tmask4 = np.zeros((si_z,si_y,si_x)) + zf[:-1].reshape(si_z,1,1)
Hsponge = 5000
tmask5 = -tmask4/Hsponge + 1
tmask5 = np.where(tmask5<0,0,tmask5)
tmask5 = tmask5**2
tmask = tmask + tmask5
#tmask[0,:,:] = 1.0

# relax lower part to lower grid point temperature
trelax = np.where(tmask4>Lz-2*H0,tinit[-1,-1,-1],tinit)
#trelax = 0*tinit + tinit[-1,-1,-1]

# upper grid point temperature
trelax[0,0,:] = tinit[0,0,:]

tmask.astype(binprec).tofile('tmask.box')
trelax.astype(binprec).tofile('trelax.box')

# relax u vel (sponge only)
urelax = 1.0*uvel;
umask = 1.0*tmask5

umask.astype(binprec).tofile('umask.box')
urelax.astype(binprec).tofile('urelax.box')


# # === vertical diffusivity
# K0 = 5. # m^2/s
# Kr  = K0 + np.zeros((si_z,si_y,si_x));
# Kr[0,:,:]  = 0 # no flux top
# Kr[-1,:,:] = 0 # no flux bottom

# Kr.astype(binprec).tofile('Kr.box')


########## OBCS files ================

# East
u_e = uvel[:,:,-1]
t_e = tinit[:,:,-1]

u_e.astype(binprec).tofile('u_E.box')
t_e.astype(binprec).tofile('t_E.box')

# West
u_w = uvel[:,:,0]
t_w = tinit[:,:,0]

u_w.astype(binprec).tofile('u_W.box')
t_w.astype(binprec).tofile('t_W.box')

J = gg*rho0z/(rho0*u0z**2)
S = H0/L0
delta = (nu/u0z/L0**2)**(1./3)

print ("J = {0}".format(J))
print ("S = {0}".format(S))
print ("delta = {0}".format(delta))
