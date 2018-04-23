import scipy as sp


def conduit_conductance(target, throat_conductance,
                        throat_occupancy='throat.occupancy',
                        pore_occupancy='pore.occupancy',
                        mode='strict', factor=1e-6):
    r"""
    Determines the conductance of a pore-throat-pore conduit based on the
    invaded state of each element.

    Parameters
    ----------
    target : OpenPNM Object
        The OpenPNM object where the model is attached.  Should either be a
        Physics or a Phase.

    throat_conductance : string
        The transport conductance of the phase associated with the ``target``
        object at single-phase conditions.

    pore_occupancy : string
        The property name containing the occupancy of the phase associated
        with the ``target`` object.  An occupancy of 1 means the pore
        is completely filled with the phase and it fully conducts.

    throat_occupancy : string
        The property name containing the occupancy of the phase associated
        with the ``target`` object.  An occupancy of 1 means the throat
        is completely filled with the phase and it fully conducts.

    mode : 'strict' or 'medium' or 'loose'
        How agressive the method should be when determining if a conduit is
        closed.

        **'strict'** :  If any pore or throat in the conduit is unoccupied by
         the given phase, the conduit is closed.

        **'medium'** : If either the throat or both pores are unoccupied, the
        conduit is closed

        **'loose'** : Only close the conduit if the throat is unoccupied

    factor : float (default is 1e-6)
        The factor which becomes multiplied to the original conduit's
        conductance to severely limit transport, but not set it to zero.

    """
    network = target.project.network
    phase = target.project.find_phase(target)
    Tinv = phase[throat_occupancy] < 0.5
    P12 = network['throat.conns']
    Pinv = phase[pore_occupancy][P12] < 0.5
    if mode == 'loose':
        mask = Tinv
    elif mode == 'medium':
        mask = Tinv + sp.all(Pinv, axis=1)
    elif mode == 'strict':
        mask = Tinv + sp.any(Pinv, axis=1)
    else:
        raise Exception('Unrecongnized mode '+mode)
    value = phase[throat_conductance]
    value[mask] = value[mask]*factor
    # Now map throats onto target object
    Ts = phase.map_throats(ids=target['throat._id'])
    return value[Ts]


def late_throat_filling(target, Pc, Swp_star=0.11, eta=3,
                        throat_entry_pressure='throat.capillary_pressure'):
    r"""
    Calculates the fraction of a throat filled with invading fluid based on
    the capillary pressure in the system.  The invading phase volume is
    calculated from:

        .. math::
            S_{nwp} = 1 - S_{wp}^{*} (P_{inv}/P_{c})^{\eta}

    Parameters
    ----------
    Pc : float
        The capillary pressure in the non-wetting phase (Pc > 0)

    eta : float
        Exponent to control the rate at which wetting phase is displaced

    Swp_star : float
        The residual wetting phase in an invaded throat immediately after
        nonwetting phase invasion

    throat_entry_pressure : string
        The dictionary key containing throat entry pressures.

    Returns
    -------
    A Nt-list of containing the fraction of each throat that is filled with
    non-wetting phase.

    """
    Swp = sp.ones(target.Nt,)
    if Pc > 0:
        Swp = Swp_star*(target[throat_entry_pressure]/Pc)**eta
    values = (1 - Swp)
    return values


def late_pore_filling(target, Pc, Swp_star=0.2, eta=3,
                      throat_entry_pressure='throat.capillary_pressure'):
    r"""
    Calculates the fraction of a pore filled with invading fluid based on
    the capillary pressure in the system.  The invading phase volume is
    calculated from:

        .. math::
            S_{nwp} = 1 - S_{wp}^{*} (P_{inv}/P_{c})^{\eta}

    Parameters
    ----------
    Pc : float`
        The capillary pressure in the non-wetting phase (Pc > 0)

    eta : float
        Exponent to control the rate at which wetting phase is displaced

    Swp_star : float
        The residual wetting phase in an invaded pore immediately after
        nonwetting phase invasion

    throat_entry_pressure : string
        The dictionary key containing throat entry pressures.
    Returns
    -------
    A Np-list of containing the fraction of each pore that is filled with non-
    wetting phase.

    """
    phase = target.project.find_phase(target)
    # Find PcStar
    from openpnm.models.misc import from_neighbor_throats
    pc_star = from_neighbor_throats(target=phase,
                                    throat_prop=throat_entry_pressure,
                                    mode='min')
    Swp = sp.ones(target.Np,)
    if Pc > 0:
        Swp = Swp_star*(pc_star/Pc)**eta
    values = (1 - Swp)
    return values
