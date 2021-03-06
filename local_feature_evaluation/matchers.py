import torch
import torch.nn.functional as func


# Mutual nearest neighbors matcher for L2 normalized descriptors.
def mutual_nn_matcher(descriptors1, descriptors2):
    device = descriptors1.device
    sim = descriptors1 @ descriptors2.t()
    nn12 = torch.max(sim, dim=1)[1]
    nn21 = torch.max(sim, dim=0)[1]
    ids1 = torch.arange(0, sim.shape[0], device=device)
    mask = ids1 == nn21[nn12]
    matches = torch.stack([ids1[mask], nn12[mask]]).t()
    return matches.data.cpu().numpy()


# Mutual nearest neighbors matcher for fusion_desc
def fusion_matcher(descriptors1, descriptors2, meta_descriptors1,
                   meta_descriptors2):
    device = descriptors1.device
    desc_weights = torch.einsum('nid,mid->nim', (meta_descriptors1, meta_descriptors2))
    del meta_descriptors1, meta_descriptors2
    desc_weights = func.softmax(desc_weights, dim=1)
    desc_sims = torch.einsum('nid,mid->nim',
                             (descriptors1, descriptors2)) * desc_weights
    del descriptors1, descriptors2, desc_weights
    desc_sims = torch.sum(desc_sims, dim=1)
    nn12 = torch.max(desc_sims, dim=1)[1]
    nn21 = torch.max(desc_sims, dim=0)[1]
    ids1 = torch.arange(desc_sims.shape[0], dtype=torch.long, device=device)
    del desc_sims
    mask = ids1 == nn21[nn12]
    matches = torch.stack([ids1[mask], nn12[mask]]).t()
    return matches.data.cpu().numpy()


# Mutual nearest neighbors matcher for fusion_desc
def sequential_fusion_matcher(descriptors1, descriptors2, meta_descriptors1,
                              meta_descriptors2):
    device = descriptors1.device
    desc_sims = 0.
    weights_sum = 0.
    for i in range(4):
        weights = torch.exp(meta_descriptors1[:, i, :]
                            @ meta_descriptors2[:, i, :].t())
        weights_sum += weights
        desc_sims += (descriptors1[:, i, :] @ descriptors2[:, i, :].t()) * weights
    del meta_descriptors1, meta_descriptors2, descriptors1, descriptors2, weights
    desc_sims /= weights_sum
    del weights_sum
    nn12 = torch.max(desc_sims, dim=1)[1]
    nn21 = torch.max(desc_sims, dim=0)[1]
    ids1 = torch.arange(0, desc_sims.shape[0], device=device)
    mask = ids1 == nn21[nn12]
    matches = torch.stack([ids1[mask], nn12[mask]]).t()
    return matches.data.cpu().numpy()
