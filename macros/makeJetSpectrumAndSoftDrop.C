#ifdef __CLING__
R__ADD_INCLUDE_PATH($FASTJET/include)
R__ADD_INCLUDE_PATH($HEPMC_ROOT/include)
R__LOAD_LIBRARY(libCGAL)
R__LOAD_LIBRARY(libCGAL_Core)
R__LOAD_LIBRARY(libfastjet)
R__LOAD_LIBRARY(libsiscone);
R__LOAD_LIBRARY(libsiscone_spherical);
R__LOAD_LIBRARY(libfastjetplugins);
R__LOAD_LIBRARY(libfastjetcontribfragile)
R__LOAD_LIBRARY(libHepMC)
R__LOAD_LIBRARY(libHepMCfio)
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

#include <HepMC/GenEvent.h>
#include <HepMC/IO_GenEvent.h>
#include <HepMC/WeightContainer.h>
#include <fastjet/PseudoJet.hh>
#include <fastjet/ClusterSequence.hh>
#include <fastjet/JetDefinition.hh>
#include <fastjet/contrib/SoftDrop.hh>
#if FASJET_VERSION_NUMBER >= 30302
#include <fastjet/tools/Recluster.hh>
#else
#include <fastjet/contrib/Recluster.hh>
#endif

std::vector<double> getZgBinning() {
    std::vector<double> binning =  {0.};
    double current = 0.1;
    while(current <= 0.5) {
        binning.push_back(current);
        current += 0.05;
    }
    return binning;
}

std::vector<double> getRgBinning(double R) {
    std::vector<double> binning =  {-0.05};
    double current = 0.0;
    while(current <= R + 0.05) {
        binning.push_back(current);
        current += 0.05;
    }
    return binning;
}

std::vector<double> getLinearBinning(double min, double max, double stepsize) {
    std::vector<double> binning;
    for(auto b = min; b <= max; b += stepsize) binning.emplace_back(b);
    return binning;
}


enum HardProcessType_t {
    kAllJets,
    kQuarkJet,
    kGluonJet,
    kUnknownJet
};

class HistogramHandler {
    public:
        enum HistType_t {
            kSpectrumAbs,
            kSpectrumWeighted,
            kZgAbs,
            kZgWeighted,
            kRgAbs,
            kRgWeighted,
            kThetagAbs,
            kThetagWeighted,
            kNsdAbs,
            kNsdWeighted
        };
        HistogramHandler() = default;
        ~HistogramHandler() = default;

        void countEvent(double kt, double weight) {
            hNevents->Fill(1);
            hAverageWeight->Fill(1., weight);
            hKtAbs->Fill(kt);
            hKtWeighted->Fill(kt, weight);
        }

        void fill(HardProcessType_t proctype, HistType_t histtype, int R, double pt, double value, double weight = 1.) {
            auto found = mData.find(R);
            if(found != mData.end()) {
                found->second.fill(proctype, histtype, pt, value, weight);
            } else {
                std::cout << "Data not found for R=" << R << std::endl;
            }
        }
        
        void build() {
            hNevents = new TH1D("hNevents", "hNevents", 1, 0.5, 1.5);
            hNevents->SetDirectory(nullptr);
            hAverageWeight = new TProfile("hXsection", "Cross section", 1, 0.5, 1.5);
            hAverageWeight->SetDirectory(nullptr);
            hKtAbs = new TH1D("hKtAbs", "event kt (abs)", 1000, 0., 1000.);
            hKtAbs->SetDirectory(nullptr);
            hKtWeighted = new TH1D("hKtWeighted", "event (weighted)", 1000, 0., 1000.);
            hKtWeighted->SetDirectory(nullptr);
            for(auto R : ROOT::TSeqI(2, 7)) {
                SoftDropRbin rb;
                rb.build(R);
                mData[R] = rb;
            }
        }

        void write(const char *filename) {
            std::unique_ptr<TFile> writer(TFile::Open(filename, "RECREATE"));
            writer->cd();
            hNevents->Write();
            hAverageWeight->Write();
            hKtAbs->Write();
            hKtWeighted->Write();
            createDirectoryStructure(*writer);
            for(auto R : ROOT::TSeqI(2, 7)) {
               mData[R].write(*writer); 
            }
        }

    private:
        class SoftDropRbin {
            public:
                struct Histos {
                    TH1 *hJetSpectrumAbs;
                    TH1 *hJetSpectrumWeighted;
                    TH2 *hZgAbs;
                    TH2 *hZgWeighted;
                    TH2 *hRgAbs;
                    TH2 *hRgWeighted;
                    TH2 *hThetagAbs;
                    TH2 *hThetagWeighted;
                    TH2 *hNsdAbs;
                    TH2 *hNsdWeighted;

                    void build(int R, HardProcessType_t proc) {
                        std::vector<double> zgbinning = getZgBinning(), nsdbinning = getLinearBinning(-1.5, 20.5, 1.), ptbinning = getLinearBinning(0., 500., 1.),
                                            thetagbinning = getLinearBinning(-0.1, 1., 0.1);
                        std::string procname, proctitle;
                        switch(proc){
                            case kAllJets: procname = "All"; proctitle = "All jets"; break;
                            case kQuarkJet: procname = "Quark"; proctitle = "Quark jets"; break;
                            case kGluonJet: procname = "Gluon"; proctitle = "Gluon jets"; break;
                            case kUnknownJet: procname = "Unknown"; proctitle = "Unknown jets"; break;
                        };

                        hJetSpectrumWeighted = new TH1D(Form("JetSpectrumWeightedR%02d%s", R, procname.data()), Form("JetSpectrum (weighted) for R=%.1f (%s)", double(R)/10., proctitle.data()), 500, 0., 500.);
                        hJetSpectrumWeighted->SetDirectory(nullptr);

                        hJetSpectrumAbs = new TH1D(Form("JetSpectrumAbsR%02d%s", R, procname.data()), Form("JetSpectrum (absolute) for R=%.1f (%s)", double(R)/10., proctitle.data()), 500, 0., 500.);
                        hJetSpectrumAbs->SetDirectory(nullptr);

                        hZgWeighted = new TH2D(Form("hZgWeightR%02d%s", R, procname.data()), Form("Zg (weighted) for R=%.1f (%s)", double(R)/10., proctitle.data()), zgbinning.size() - 1, zgbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hZgWeighted->SetDirectory(nullptr);

                        hZgAbs = new TH2D(Form("hZgAbsR%02d%s", R, procname.data()), Form("Zg (absolute) for R=%.1f (%s)", double(R)/10., proctitle.data()), zgbinning.size() - 1, zgbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hZgAbs->SetDirectory(nullptr);

                        std::vector<double> rgbinning = getRgBinning(double(R)/10.);
                        hRgWeighted = new TH2D(Form("hRgWeightR%02d%s", R, procname.data()), Form("Rg (weighted) for R=%.1f (%s)", double(R)/10., proctitle.data()), rgbinning.size() - 1, rgbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hRgWeighted->SetDirectory(nullptr);

                        hRgAbs = new TH2D(Form("hRgAbsR%02d%s", R, procname.data()), Form("Rg (absolute) for R=%.1f (%s)", double(R)/10., proctitle.data()), rgbinning.size() - 1, rgbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hRgAbs->SetDirectory(nullptr);

                        hNsdWeighted = new TH2D(Form("hNsdWeightR%02d%s", R, procname.data()), Form("Nsd (weighted) for R=%.1f (%s)", double(R)/10., proctitle.data()), nsdbinning.size() - 1, nsdbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hNsdWeighted->SetDirectory(nullptr);

                        hNsdAbs = new TH2D(Form("hNsdAbsR%02d%s", R, procname.data()), Form("Nsd (absolute) for R=%.1f (%s)", double(R)/10., proctitle.data()), nsdbinning.size() - 1, nsdbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hNsdAbs->SetDirectory(nullptr);

                        hThetagWeighted = new TH2D(Form("hThetagWeightR%02d%s", R, procname.data()), Form("#Thetag (weighted) for R=%.1f (%s)", double(R)/10., proctitle.data()), thetagbinning.size() - 1, thetagbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hThetagWeighted->SetDirectory(nullptr);

                        hThetagAbs = new TH2D(Form("hThetagAbsR%02d%s", R, procname.data()), Form("#Thetag (absolute) for R=%.1f (%s)", double(R)/10., proctitle.data()), thetagbinning.size() - 1, thetagbinning.data(), ptbinning.size() -1, ptbinning.data());
                        hThetagAbs->SetDirectory(nullptr);
                    }
                    
                    void fill(HistType_t histtype, double pt, double value, double weight = 1.) {
                        switch(histtype) {
                            case kSpectrumAbs: hJetSpectrumAbs->Fill(pt); break;
                            case kSpectrumWeighted: hJetSpectrumWeighted->Fill(pt, weight); break;
                            case kZgAbs: hZgAbs->Fill(value, pt); break;
                            case kZgWeighted: hZgWeighted->Fill(value, pt, weight); break;
                            case kRgAbs: hRgAbs->Fill(value, pt); break;
                            case kRgWeighted: hRgWeighted->Fill(value, pt, weight); break;
                            case kThetagAbs: hThetagAbs->Fill(value, pt); break;
                            case kThetagWeighted: hThetagWeighted->Fill(value, pt, weight); break;
                            case kNsdAbs: hNsdAbs->Fill(value, pt); break;
                            case kNsdWeighted: hNsdWeighted->Fill(value, pt, weight); break;
                            default: std::cout << "Unknown hist type: " << histtype << std::endl;
                        };
                    }

                    void write(TFile &writer) {
                        writer.cd("Spectra"); 
                        hJetSpectrumAbs->Write();
                        hJetSpectrumWeighted->Write();
                        writer.cd("Zg"); 
                        hZgAbs->Write();
                        hZgWeighted->Write();
                        writer.cd("Rg"); 
                        hRgAbs->Write();
                        hRgWeighted->Write();
                        writer.cd("Thetag"); 
                        hThetagAbs->Write();
                        hThetagWeighted->Write();
                        writer.cd("Nsd"); 
                        hNsdAbs->Write();
                        hNsdWeighted->Write();
                    }
                };
                SoftDropRbin() = default;
                ~SoftDropRbin() = default;

                void build(int R) {
                    std::vector<HardProcessType_t> procs = {kAllJets, kQuarkJet, kGluonJet, kUnknownJet};
                    for(auto proc : procs) {
                        Histos prochists;
                        prochists.build(R, proc);
                        mRdata[proc] = prochists;
                    }
                }

                void fill(HardProcessType_t proctype, HistType_t histtype, double pt, double value, double weight = 1.) {
                    auto found = mRdata.find(proctype);
                    if(found != mRdata.end()) {
                        found->second.fill(histtype, pt, value, weight);
                    } else {
                        std::cout << "Histos not found for proc type " << proctype << std::endl;
                    }
                }

                void write(TFile &reader) {
                    std::vector<HardProcessType_t> procs = {kAllJets, kQuarkJet, kGluonJet, kUnknownJet};
                    for(auto proc : procs) {
                        mRdata[proc].write(reader);
                    }
                }

            private:
                std::map<HardProcessType_t, Histos> mRdata;

        };

        void createDirectoryStructure(TFile &writer) {
            std::vector<std::string> observables = {"Spectra", "Zg", "Rg", "Nsd", "Thetag"};
            for(auto obs : observables){
                writer.mkdir(obs.data());
            }
        }

        TH1 *hNevents;
        TProfile *hAverageWeight;
        TH1 *hKtAbs;
        TH1 *hKtWeighted;
        std::map<int, SoftDropRbin> mData;
};

class HepMCConstituent : public fastjet::PseudoJet::UserInfoBase {
    public:
        HepMCConstituent(HepMC::GenParticle *particle) : 
            fastjet::PseudoJet::UserInfoBase(), 
            mParticle(particle)
        {

        }

        HepMC::GenParticle *getParticle() const { return mParticle; }
    private:
        HepMC::GenParticle *mParticle;
};

struct PartonMother {
    HepMC::GenParticle *mMotherParticle;
    int mCount;
};

struct SoftDropData {
    double Zg;
    double Rg;
    int DropCount;
};

bool isFinalState(const HepMC::GenParticle* p) { 
    if ( !p->end_vertex() && p->status()==1 ) return true;
    return false;
}

std::vector<fastjet::PseudoJet> select_particles(HepMC::GenEvent &event) {
    std::vector<fastjet::PseudoJet> result;
    for(auto partit = event.particles_begin(); partit != event.particles_end(); ++partit) {
        auto particle = *partit;
        if(!isFinalState(particle)) continue;
        auto partmom = particle->momentum();
        if(std::abs(partmom.eta()) > 0.7) continue;
        fastjet::PseudoJet jetparticle{partmom.px(), partmom.py(), partmom.pz(), partmom.e()};
        jetparticle.set_user_info(new HepMCConstituent(particle));
        result.emplace_back(jetparticle);
    }
    return result;
}

std::vector<HepMC::GenParticle *> getMotherParticles(const HepMC::GenVertex *prodvtx) {
    std::vector<HepMC::GenParticle *> mothers;
    if(!prodvtx) {
        std::cout << "No production vertex found for current particle" << std::endl;
        return mothers;
    }
    for(auto motheriter = prodvtx->particles_in_const_begin(); motheriter < prodvtx->particles_in_const_end(); motheriter++) {
        mothers.push_back(*motheriter);
    }
    return mothers;
}

bool isDiquark(int abspdg) {
    const std::array<int, 25> diquarks = {{1103, 2101, 2103, 2203, 3101, 3103, 3201, 3203, 3303, 4101, 4103, 4201, 4203, 4301, 4303, 4403, 5101, 5103, 5201, 5203, 5301, 5303, 5401, 5403, 5503}};
    return std::find(diquarks.begin(), diquarks.end(), abspdg) != diquarks.end();
}

HepMC::GenParticle *getPartonOrigin(const fastjet::PseudoJet &recjet) {
    std:vector<PartonMother> partons;
    for(const auto &jetparticle : recjet.constituents()) {
        HepMC::GenParticle *current_Particle = dynamic_cast<const HepMCConstituent *>(jetparticle.user_info_ptr())->getParticle(),
                           *chainstart = current_Particle;
        std::vector<HepMC::GenParticle *> motherparticles = getMotherParticles(current_Particle->production_vertex());
        bool found = false;
        int chainlength = 1;
        while(!found) {
            // hard process should have at min. 2 mothers (either 2 gluons from gluon fusion or two quarks or quark-gluon from the beam particles)
            if(!motherparticles.size()) {
                std::cout << "Failed getting mother particles: current id " << current_Particle->pdg_id() 
                          << ", start " << chainstart->pdg_id() << " (" << chainstart->momentum().px() << "," << chainstart->momentum().py() << "," << chainstart->momentum().pz() 
                          << "), length " << chainlength << std::endl;
                current_Particle = nullptr;
                break;
            }
            current_Particle = motherparticles[0];
            int abspdg = std::abs(current_Particle->pdg_id());
            if(abspdg == kGluon || (abspdg >= kDown && abspdg <= kTop)) {
                // mother particle either quark or gluon, breaking
                found = true;
            } else if(isDiquark(abspdg)) {
                found = true;
            } else {
                motherparticles = getMotherParticles(current_Particle->production_vertex());
                chainlength++;
            }
        }
        if(!current_Particle) {
            std::cerr << "No mother particle found for chain" << std::endl;
        } else {
            auto found = std::find_if(partons.begin(), partons.end(), [current_Particle](const PartonMother &mother) { return *(mother.mMotherParticle) == *current_Particle; } );
            if(found != partons.end() ){
                found->mCount += 1;
            } else {
                PartonMother nextmother{current_Particle, 1};
                partons.push_back(nextmother);
            }
        }
    }
    if(!partons.size()) return nullptr;
    // Take parton with the highest energy as source 
    std::sort(partons.begin(), partons.end(), [](const PartonMother &lhs, const PartonMother &rhs) { return lhs.mMotherParticle->momentum().e() > rhs.mMotherParticle->momentum().e(); });
    return partons[0].mMotherParticle;
}

SoftDropData makeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius) {
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
    return {sym < 0. ? 0. : sym , softdropstruct.delta_R(), softdropstruct.dropped_count()};
}

std::vector<SoftDropData> makeIterativeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius) {
    double beta = 0, fZcut = 0.1;
    std::vector<SoftDropData> result;
    fastjet::JetDefinition fJetDef(fastjet::cambridge_algorithm, 1., static_cast<fastjet::RecombinationScheme>(0), fastjet::BestFJ30 ); 
    fastjet::ClusterSequence recluster(constituents, fJetDef);
    auto outputJets = recluster.inclusive_jets(0);
    fastjet::PseudoJet harder, softer, splitting = outputJets[0];

    int drop_count = 0;
    while(splitting.has_parents(harder,softer)){
      if(harder.perp() < softer.perp()) std::swap(harder,softer);
      drop_count += 1;
      auto sym = softer.perp()/(harder.perp()+softer.perp()),
           geoterm = beta > 0 ? std::pow(harder.delta_R(softer) / jetradius, beta) : 1.,
           zcut = fZcut * geoterm; 
      if(sym > zcut) {
        // accept splitting
        double mu2 = TMath::Abs(splitting.m2()) < 1e-5 ? 100000. : std::max(harder.m2(), softer.m2())/splitting.m2();
        SoftDropData acceptedSplitting{
          sym,
          harder.delta_R(softer),
          drop_count 
        };
        result.push_back(acceptedSplitting);
      }
      splitting = harder;
    }
    return result;
}

HardProcessType_t getHardProcessType(HepMC::GenParticle *parton) {
    HardProcessType_t proctype = HardProcessType_t::kUnknownJet;
    if(!parton) return proctype;
    int pdgcode = std::abs(parton->pdg_id());
    if(pdgcode == std::abs(kGluon)) proctype = kGluonJet;
    else if(isDiquark(pdgcode)) proctype = kGluonJet;   /// treat diquarks as gluon decays
    else if(pdgcode >= std::abs(kDown) && pdgcode <= std::abs(kTop)) proctype = kQuarkJet;
    return proctype;
}

void makeJetSpectrumAndSoftDrop(const char *inputfile = "events.hepmc", int maxevents = -1){
    HistogramHandler histos;
    histos.build();
    HepMC::IO_GenEvent hepmcreader(inputfile, std::ios::in);
    auto event = hepmcreader.read_next_event();
    int eventcounter = 0;
    while(event) {
        auto weight = event->cross_section()->cross_section() * 1e-9; // in mb
        histos.countEvent(event->event_scale(), weight);
        auto particlesForJetfinding = select_particles(*event);
        for(auto R : ROOT::TSeqI(2, 7)) {
            double jetradius = double(R)/10.;
            fastjet::ClusterSequence jetfinder(particlesForJetfinding, fastjet::JetDefinition(fastjet::antikt_algorithm, jetradius, fastjet::E_scheme));
            auto incjets = fastjet::sorted_by_pt(jetfinder.inclusive_jets());
            for(auto jet : incjets) {
                if(std::abs(jet.eta()) > 0.7 - jetradius) continue;
                if(jet.pt() > 3 * event->event_scale()) continue; // outlier cut
                HepMC::GenParticle *hardParton = getPartonOrigin(jet);
                auto proctyoe = getHardProcessType(hardParton);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kSpectrumWeighted, R, jet.pt(), 1., weight);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kSpectrumAbs, R, jet.pt(), 1., 1.);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kSpectrumWeighted, R, jet.pt(), 1., weight);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kSpectrumAbs, R, jet.pt(), 1., 1.);
                auto softdropresults = makeSoftDrop(jet.constituents(), jetradius);
                auto iterativeSoftdropresults = makeIterativeSoftDrop(jet.constituents(), jetradius);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kZgWeighted, R, jet.pt(), softdropresults.Zg, weight);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kZgAbs, R, jet.pt(), softdropresults.Zg, 1.);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kZgWeighted, R, jet.pt(), softdropresults.Zg, weight);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kZgAbs, R, jet.pt(), softdropresults.Zg, 1.);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kRgWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg, weight);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kRgAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg, 1.);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kRgWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg, weight);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kRgAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg, 1.);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kRgWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size(), weight);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kRgAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size(), 1.);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kRgWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size(), weight);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kRgAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -1. : iterativeSoftdropresults.size(), 1.);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kThetagWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg/jetradius, weight);
                histos.fill(HardProcessType_t::kAllJets, HistogramHandler::HistType_t::kThetagAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg/jetradius, 1.);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kThetagWeighted, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg/jetradius, weight);
                histos.fill(proctyoe, HistogramHandler::HistType_t::kThetagAbs, R, jet.pt(), softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg/jetradius, 1.);
            }
        }
        delete event;
        event = hepmcreader.read_next_event();       
        eventcounter++;
        if(maxevents > -1 && eventcounter >= maxevents) {
            std::cout << "stopped event loop after " << eventcounter << " events ..." << std::endl;
            break;
        }
    }
    delete event;
    std::cout << "Done" << std::endl;

    histos.write("AnalysisResults.root");
}