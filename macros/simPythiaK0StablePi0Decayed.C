#ifdef __CLING__
R__ADD_INCLUDE_PATH($FASTJET / include)
R__ADD_INCLUDE_PATH($PYTHIA_ROOT / include)
R__LOAD_LIBRARY(libpythia8)
R__LOAD_LIBRARY(libCGAL)
R__LOAD_LIBRARY(libCGAL_Core)
R__LOAD_LIBRARY(libfastjet)
R__LOAD_LIBRARY(libsiscone);
R__LOAD_LIBRARY(libsiscone_spherical);
R__LOAD_LIBRARY(libfastjetplugins);
R__LOAD_LIBRARY(libfastjetcontribfragile)
#else
#include <cmath>
#include <map>
#include <memory>
#include <TFile.h>
#include <TProfile.h>
#include <TH1.h>
#include <TH2.h>
#include <ROOT/TSeq.hxx>
#include <TPDGCode.h>
#endif

#include "Pythia8/Pythia.h"
#include "Pythia8/Event.h"
#include "Pythia8/Info.h"

#include <fastjet/PseudoJet.hh>
#include <fastjet/ClusterSequence.hh>
#include <fastjet/JetDefinition.hh>
#include <fastjet/contrib/SoftDrop.hh>
#if FASJET_VERSION_NUMBER >= 30302
#include <fastjet/tools/Recluster.hh>
#else
#include <fastjet/contrib/Recluster.hh>
#endif

std::vector<double> getZgBinning()
{
  std::vector<double> binning = {0.};
  double current = 0.1;
  while (current <= 0.5)
  {
    binning.push_back(current);
    current += 0.05;
  }
  return binning;
}

std::vector<double> getRgBinning(double R)
{
  std::vector<double> binning = {-0.05};
  double current = 0.0;
  while (current <= R + 0.05)
  {
    binning.push_back(current);
    current += 0.05;
  }
  return binning;
}

std::vector<double> getLinearBinning(double min, double max, double stepsize)
{
  std::vector<double> binning;
  for (auto b = min; b <= max; b += stepsize)
    binning.emplace_back(b);
  return binning;
}

enum HardProcessType_t
{
  kAllJets,
  kQuarkJet,
  kGluonJet,
  kUnknownJet
};

class HistogramHandler
{
public:
  enum HistType_t
  {
    kSpectrum,
    kZg,
    kRg,
    kThetag,
    kNsd,
  };
  HistogramHandler() = default;
  ~HistogramHandler() = default;

  void countEvent(int pthardbin, double eventscale, double pthard, double crosssection, int trials)
  {
    hNevents->Fill(pthardbin);
    hCrossSection->Fill(pthardbin, crosssection);
    hTrials->Fill(pthardbin, trials);
    hPtHard->Fill(pthard);
    hEventScale->Fill(eventscale);
  }

  void fill(HardProcessType_t proctype, HistType_t histtype, int R, double pt, double value)
  {
    auto found = mData.find(R);
    if (found != mData.end())
    {
      found->second.fill(proctype, histtype, pt, value);
    }
    else
    {
      std::cout << "Data not found for R=" << R << std::endl;
    }
  }

  void fillPi0(double pt) { hSpecConstPi0->Fill(pt); }

  void fillK0(double pt) { hSpecConstK0->Fill(pt); }

  void build()
  {
    hNevents = new TH1D("hNevents", "hNevents", 21, -0.5, 20.5);
    hNevents->SetDirectory(nullptr);
    hCrossSection = new TProfile("hXsection", "Cross section", 21, -0.5, 20.5);
    hCrossSection->SetDirectory(nullptr);
    hTrials = new TH1D("hTrials", "hTrials", 21, -0.5, 20.5);
    hTrials->SetDirectory(nullptr);
    hPtHard = new TH1D("hPtHard", "pt-hard", 1000, 0., 1000.);
    hPtHard->SetDirectory(nullptr);
    hEventScale = new TH1D("hEventScale", "event scale", 1000, 0., 1000.);
    hEventScale->SetDirectory(nullptr);
    hSpecConstPi0 = new TH1D("hSpecConstPi0", "Spectrum of selected constituent pi0", 1000, 0., 1000.);
    hSpecConstPi0->SetDirectory(nullptr);
    hSpecConstK0 = new TH1D("hSpecConstK0", "Spectrum of selected constituent K0", 1000, 0., 1000.);
    hSpecConstK0->SetDirectory(nullptr);
    for (auto R : ROOT::TSeqI(2, 7))
    {
      SoftDropRbin rb;
      rb.build(R);
      mData[R] = rb;
    }
  }

  void write(const char *filename)
  {
    std::unique_ptr<TFile> writer(TFile::Open(filename, "RECREATE"));
    writer->cd();
    hNevents->Write();
    hCrossSection->Write();
    hTrials->Write();
    hPtHard->Write();
    hEventScale->Write();
    hSpecConstPi0->Write();
    hSpecConstK0->Write();
    createDirectoryStructure(*writer);
    for (auto R : ROOT::TSeqI(2, 7))
    {
      mData[R].write(*writer);
    }
  }

private:
  class SoftDropRbin
  {
  public:
    struct Histos
    {
      TH1 *hJetSpectrum;
      TH2 *hZg;
      TH2 *hRg;
      TH2 *hThetag;
      TH2 *hNsd;

      void build(int R, HardProcessType_t proc)
      {
        std::vector<double> zgbinning = getZgBinning(), nsdbinning = getLinearBinning(-1.5, 20.5, 1.), ptbinning = getLinearBinning(0., 500., 1.),
                            thetagbinning = getLinearBinning(-0.1, 1., 0.1);
        std::string procname, proctitle;
        switch (proc)
        {
        case kAllJets:
          procname = "All";
          proctitle = "All jets";
          break;
        case kQuarkJet:
          procname = "Quark";
          proctitle = "Quark jets";
          break;
        case kGluonJet:
          procname = "Gluon";
          proctitle = "Gluon jets";
          break;
        case kUnknownJet:
          procname = "Unknown";
          proctitle = "Unknown jets";
          break;
        };

        hJetSpectrum = new TH1D(Form("JetSpectrumR%02d%s", R, procname.data()), Form("JetSpectrum for R=%.1f (%s)", double(R) / 10., proctitle.data()), 500, 0., 500.);
        hJetSpectrum->SetDirectory(nullptr);

        hZg = new TH2D(Form("hZgR%02d%s", R, procname.data()), Form("Zg for R=%.1f (%s)", double(R) / 10., proctitle.data()), zgbinning.size() - 1, zgbinning.data(), ptbinning.size() - 1, ptbinning.data());
        hZg->SetDirectory(nullptr);

        std::vector<double> rgbinning = getRgBinning(double(R) / 10.);
        hRg = new TH2D(Form("hRgAbsR%02d%s", R, procname.data()), Form("Rg for R=%.1f (%s)", double(R) / 10., proctitle.data()), rgbinning.size() - 1, rgbinning.data(), ptbinning.size() - 1, ptbinning.data());
        hRg->SetDirectory(nullptr);

        hNsd = new TH2D(Form("hNsdAbsR%02d%s", R, procname.data()), Form("Nsd for R=%.1f (%s)", double(R) / 10., proctitle.data()), nsdbinning.size() - 1, nsdbinning.data(), ptbinning.size() - 1, ptbinning.data());
        hNsd->SetDirectory(nullptr);

        hThetag = new TH2D(Form("hThetagAbsR%02d%s", R, procname.data()), Form("#Thetag for R=%.1f (%s)", double(R) / 10., proctitle.data()), thetagbinning.size() - 1, thetagbinning.data(), ptbinning.size() - 1, ptbinning.data());
        hThetag->SetDirectory(nullptr);
      }

      void fill(HistType_t histtype, double pt, double value)
      {
        switch (histtype)
        {
        case kSpectrum:
          hJetSpectrum->Fill(pt);
          break;
        case kZg:
          hZg->Fill(value, pt);
          break;
        case kRg:
          hRg->Fill(value, pt);
          break;
        case kThetag:
          hThetag->Fill(value, pt);
          break;
        case kNsd:
          hNsd->Fill(value, pt);
          break;
        default:
          std::cout << "Unknown hist type: " << histtype << std::endl;
        };
      }

      void write(TFile &writer)
      {
        writer.cd("Spectra");
        hJetSpectrum->Write();
        writer.cd("Zg");
        hZg->Write();
        writer.cd("Rg");
        hRg->Write();
        writer.cd("Thetag");
        hThetag->Write();
        writer.cd("Nsd");
        hNsd->Write();
      }
    };
    SoftDropRbin() = default;
    ~SoftDropRbin() = default;

    void build(int R)
    {
      std::vector<HardProcessType_t> procs = {kAllJets, kQuarkJet, kGluonJet, kUnknownJet};
      for (auto proc : procs)
      {
        Histos prochists;
        prochists.build(R, proc);
        mRdata[proc] = prochists;
      }
    }

    void fill(HardProcessType_t proctype, HistType_t histtype, double pt, double value)
    {
      auto found = mRdata.find(proctype);
      if (found != mRdata.end())
      {
        found->second.fill(histtype, pt, value);
      }
      else
      {
        std::cout << "Histos not found for proc type " << proctype << std::endl;
      }
    }

    void write(TFile &reader)
    {
      std::vector<HardProcessType_t> procs = {kAllJets, kQuarkJet, kGluonJet, kUnknownJet};
      for (auto proc : procs)
      {
        mRdata[proc].write(reader);
      }
    }

  private:
    std::map<HardProcessType_t, Histos> mRdata;
  };

  void createDirectoryStructure(TFile &writer)
  {
    std::vector<std::string> observables = {"Spectra", "Zg", "Rg", "Nsd", "Thetag"};
    for (auto obs : observables)
    {
      writer.mkdir(obs.data());
    }
  }

  TH1 *hNevents;
  TProfile *hCrossSection;
  TH1 *hTrials;
  TH1 *hPtHard;
  TH1 *hEventScale;
  TH1 *hSpecConstPi0;
  TH1 *hSpecConstK0;
  std::map<int, SoftDropRbin> mData;
};

class PythiaConstituent : public fastjet::PseudoJet::UserInfoBase
{
public:
  PythiaConstituent(Pythia8::Particle *particle) : fastjet::PseudoJet::UserInfoBase(),
                                                   mParticle(particle)
  {
  }

  Pythia8::Particle *getParticle() const { return mParticle; }

private:
  Pythia8::Particle *mParticle;
};

struct PartonMother
{
  Pythia8::Particle *mMotherParticle;
  int mCount;
};

struct SoftDropData
{
  double Zg;
  double Rg;
  int DropCount;
};

bool isFinalState(const Pythia8::Particle &p)
{
  return p.isFinal();
}

std::vector<fastjet::PseudoJet> select_particles(Pythia8::Event &event, double phimin = -1., double phimax = -1)
{
  std::vector<fastjet::PseudoJet> result;
  for (auto partit = event.begin(); partit != event.end(); ++partit)
  {
    auto &particle = *partit;
    if (!isFinalState(particle))
      continue;
    if (std::abs(particle.eta()) > 0.7)
      continue;
    if (phimin >= 0. && phimax >= 0.) {
      double phival = TVector2::Phi_0_2pi(particle.phi());
      if(!(phival >= phimin && phival <= phimax)) continue;
    }
    fastjet::PseudoJet jetparticle{particle.px(), particle.py(), particle.pz(), particle.e()};
    jetparticle.set_user_info(new PythiaConstituent(&particle));
    result.emplace_back(jetparticle);
  }
  return result;
}

Pythia8::Particle *getPartonOrigin(const fastjet::PseudoJet &recjet, Pythia8::Event &event)
{
  std::vector<PartonMother> partons;
  for (const auto &jetparticle : recjet.constituents())
  {
    Pythia8::Particle *current_Particle = dynamic_cast<const PythiaConstituent *>(jetparticle.user_info_ptr())->getParticle(),
                      *chainstart = current_Particle;
    auto motherIndices = current_Particle->motherList();
    bool found = false;
    int chainlength = 1;
    while (!found)
    {
      // hard process should have at min. 2 mothers (either 2 gluons from gluon fusion or two quarks or quark-gluon from the beam particles)
      if (!motherIndices.size())
      {
        std::cout << "Failed getting mother particles: current id " << current_Particle->id()
                  << ", start " << chainstart->id() << " (" << chainstart->px() << "," << chainstart->py() << "," << chainstart->pz()
                  << "), length " << chainlength << std::endl;
        current_Particle = nullptr;
        break;
      }
      current_Particle = &(event.at(motherIndices[0]));
      if (current_Particle->isGluon() || current_Particle->isQuark() || current_Particle->isDiquark())
      {
        // mother particle either quark or gluon, breaking
        found = true;
      }
      else
      {
        motherIndices = current_Particle->motherList();
        chainlength++;
      }
    }
    if (!current_Particle)
    {
      std::cerr << "No mother particle found for chain" << std::endl;
    }
    else
    {
      auto found = std::find_if(partons.begin(), partons.end(), [current_Particle](const PartonMother &mother)
                                { return mother.mMotherParticle == current_Particle; });
      if (found != partons.end())
      {
        found->mCount += 1;
      }
      else
      {
        PartonMother nextmother{current_Particle, 1};
        partons.push_back(nextmother);
      }
    }
  }
  if (!partons.size())
    return nullptr;
  // Take parton with the highest energy as source
  std::sort(partons.begin(), partons.end(), [](const PartonMother &lhs, const PartonMother &rhs)
            { return lhs.mMotherParticle->e() > rhs.mMotherParticle->e(); });
  return partons[0].mMotherParticle;
}

SoftDropData makeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius)
{
  fastjet::JetDefinition jetdef(fastjet::antikt_algorithm, jetradius * 2, fastjet::E_scheme, fastjet::BestFJ30);
  fastjet::ClusterSequence jetfinder(constituents, jetdef);
  std::vector<fastjet::PseudoJet> outputjets = jetfinder.inclusive_jets(0);
  auto sdjet = outputjets[0];
  fastjet::contrib::SoftDrop softdropAlgorithm(0, 0.1, jetradius);
  softdropAlgorithm.set_verbose_structure(true);
  fastjet::JetAlgorithm reclusterizingAlgorithm = fastjet::cambridge_aachen_algorithm;
#if FASTJET_VERSION_NUMBER >= 30302
  fastjet::Recluster reclusterizer(reclusterizingAlgorithm, 1, fastjet::Recluster::keep_only_hardest);
#else
  fastjet::contrib::Recluster reclusterizer(reclusterizingAlgorithm, 1, true);
#endif
  softdropAlgorithm.set_reclustering(true, &reclusterizer);
  auto groomed = softdropAlgorithm(sdjet);
  auto softdropstruct = groomed.structure_of<fastjet::contrib::SoftDrop>();
  auto sym = softdropstruct.symmetry();
  return {sym < 0. ? 0. : sym, softdropstruct.delta_R(), softdropstruct.dropped_count()};
}

std::vector<SoftDropData> makeIterativeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius)
{
  double beta = 0, fZcut = 0.1;
  std::vector<SoftDropData> result;
  fastjet::JetDefinition fJetDef(fastjet::cambridge_algorithm, 1., static_cast<fastjet::RecombinationScheme>(0), fastjet::BestFJ30);
  fastjet::ClusterSequence recluster(constituents, fJetDef);
  auto outputJets = recluster.inclusive_jets(0);
  fastjet::PseudoJet harder, softer, splitting = outputJets[0];

  int drop_count = 0;
  while (splitting.has_parents(harder, softer))
  {
    if (harder.perp() < softer.perp())
      std::swap(harder, softer);
    drop_count += 1;
    auto sym = softer.perp() / (harder.perp() + softer.perp()),
         geoterm = beta > 0 ? std::pow(harder.delta_R(softer) / jetradius, beta) : 1.,
         zcut = fZcut * geoterm;
    if (sym > zcut)
    {
      // accept splitting
      double mu2 = TMath::Abs(splitting.m2()) < 1e-5 ? 100000. : std::max(harder.m2(), softer.m2()) / splitting.m2();
      SoftDropData acceptedSplitting{
          sym,
          harder.delta_R(softer),
          drop_count};
      result.push_back(acceptedSplitting);
    }
    splitting = harder;
  }
  return result;
}

HardProcessType_t getHardProcessType(const Pythia8::Particle *parton)
{
  HardProcessType_t proctype = HardProcessType_t::kUnknownJet;
  if (!parton)
    return proctype;
  if (parton->isGluon())
    proctype = kGluonJet;
  else if (parton->isDiquark())
    proctype = kGluonJet; /// treat diquarks as gluon decays
  else if (parton->isQuark())
    proctype = kQuarkJet;
  return proctype;
}

void configureK0Pi0(Pythia8::Pythia *pythia) {
    // Decays: Pi0 and K0: On
  pythia->readString("111:mayDecay  = on");
  pythia->readString("310:mayDecay  = off");
}

Pythia8::Pythia *configurePythia(int pthardbin, double ecms, int seed)
{
  std::array<std::pair<double, double>, 21> pthardbins = {{{0., 5.}, {5., 7.}, {7., 9.}, {9., 12.}, {12., 16.}, {16., 21.}, {21., 28.}, {28., 36.}, {36., 45.}, {45., 57.}, {57., 70.}, {70., 85.}, {85., 99.}, {99., 115.}, {115., 132.}, {132., 150.}, {150., 169.}, {169., 190.}, {190, 212.}, {212., 235.}, {235., 1000.}}};
  double ptmin = pthardbins[pthardbin].first, ptmax = pthardbins[pthardbin].second;
  auto pythia = new Pythia8::Pythia();

  // seed
  pythia->readString("Random:setSeed = on");
  pythia->readString(Form("Random:seed = %d", (seed % 900000000) + 1));

  // beam particles
  int idAin = kProton, idBin = kProton;
  pythia->readString(Form("Beams:eCM = %13.4f", ecms));
  pythia->readString(Form("Beams:idA = %10d", idAin));
  pythia->readString(Form("Beams:idB = %10d", idBin));

  configureK0Pi0(pythia);

  // Decays: long-lived off
  pythia->readString("3122:mayDecay = off");
  pythia->readString("3112:mayDecay = off");
  pythia->readString("3222:mayDecay = off");
  pythia->readString("3312:mayDecay = off");
  pythia->readString("3322:mayDecay = off");
  pythia->readString("3334:mayDecay = off");

  pythia->readString("SoftQCD:elastic = off");
  pythia->readString("HardQCD:all = on");

  pythia->readString(Form("PhaseSpace:pTHatMin = %13.3f", ptmin));
  pythia->readString(Form("PhaseSpace:pTHatMax = %13.3f", ptmax));
  pythia->init();
  return pythia;
}

void simPythiaK0StablePi0Decayed(int pthardbin, int seed, double ecms = 13000., int maxevents = 100000)
{
  bool cutPhiPart = true;
  const double phimin_emcal = 1.3962634,
               phimax_emcal = 3.2836121;
  HistogramHandler histos;
  histos.build();
  std::unique_ptr<Pythia8::Pythia> pythia(configurePythia(pthardbin, ecms, seed));
  for (int ievent = 0; ievent < maxevents; ievent++)
  {
    pythia->next();
    auto event = pythia->event;
    auto trials = pythia->info.nTried();
    auto crosssection = pythia->info.sigmaGen(),
         eventscale = pythia->event.scale(),
         pthard = pythia->info.pTHat();
    //->cross_section()->cross_section() * 1e-9; // in mb
    histos.countEvent(pthardbin, eventscale, pthard, crosssection, trials);
    double phimin = cutPhiPart ? phimin_emcal : -1.,
           phimax = cutPhiPart ? phimax_emcal : -1.;
    auto particlesForJetfinding = select_particles(event, phimin, phimax);
    for(auto &part : particlesForJetfinding) {
      auto partInfo = dynamic_cast<const PythiaConstituent *>(part.user_info_ptr())->getParticle();
      if(std::abs(partInfo->id()) == 111) histos.fillPi0(partInfo->pT());
      if(std::abs(partInfo->id()) == 310) histos.fillK0(partInfo->pT());
    }
    for (auto R : ROOT::TSeqI(2, 7))
    {
      double jetradius = double(R) / 10.;
      fastjet::ClusterSequence jetfinder(particlesForJetfinding, fastjet::JetDefinition(fastjet::antikt_algorithm, jetradius, fastjet::E_scheme));
      auto incjets = fastjet::sorted_by_pt(jetfinder.inclusive_jets());
      for (auto jet : incjets)
      {
        if (std::abs(jet.eta()) > 0.7 - jetradius)
          continue;
        if (jet.pt() > 3 * pthard)
          continue; // outlier cut
        Pythia8::Particle *hardParton = getPartonOrigin(jet, event);
        auto proctyoe = getHardProcessType(hardParton);
        histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kSpectrum, R, jet.pt(), 1.);
        histos.fill(proctyoe, HistogramHandler::HistType_t::kSpectrum, R, jet.pt(), 1.);
        auto softdropresults = makeSoftDrop(jet.constituents(), jetradius);
        auto iterativeSoftdropresults = makeIterativeSoftDrop(jet.constituents(), jetradius);
        histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kZg, R, jet.pt(), softdropresults.Zg);
        histos.fill(proctyoe, HistogramHandler::HistType_t::kZg, R, jet.pt(), softdropresults.Zg);
        histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kRg, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg);
        histos.fill(proctyoe, HistogramHandler::HistType_t::kRg, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg);
        histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kNsd, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size());
        histos.fill(proctyoe, HistogramHandler::HistType_t::kNsd, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size());
        histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kThetag, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg / jetradius);
        histos.fill(proctyoe, HistogramHandler::HistType_t::kThetag, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg / jetradius);
      }
    }
  }
  std::cout << "Done" << std::endl;

  histos.write("AnalysisResults.root");
}