#ifndef __CLING__
#include <iostream>

#include "TCollection.h"
#include "TFile.h"
#include "TH1.h"
#include "THnSparse.h"
#include "TKey.h"
#include "TList.h"
#include "TProfile.h"
#include "TString.h"
#include "ROOT/TSeq.hxx"
#endif

double getweight(TH1 *xsechist, TH1 *trialshist) {
	int bin = -1;
	for(auto ib : ROOT::TSeqI(0, trialshist->GetXaxis()->GetNbins())){
		if(trialshist->GetBinContent(ib+1)) {
			bin = ib+1;
			break;
		}
	}
	std::cout << "Using bin " << bin << std::endl;
	return xsechist->GetBinContent(bin)/trialshist->GetBinContent(bin);
}

void scaleRecursive(TCollection *in, double weight) {
	for(auto obj : *in) {
		auto col = dynamic_cast<TCollection *>(obj);
		if(col) {
			scaleRecursive(col, weight);	
		} else {
			auto hist = dynamic_cast<TH1 *>(obj);
			if(hist) {
				hist->Scale(weight);
			} else {
				auto sparse = dynamic_cast<THnSparse *>(obj);
				if(sparse){
					sparse->Scale(weight);
				}
			}
		}
	}
}

void makeScaled(const char *filename = "AnalysisResults.root"){
	std::unique_ptr<TFile> reader(TFile::Open(filename, "READ")),
	                       writer(TFile::Open("AnalysisResults_scaled.root", "RECREATE"));
	auto xsechist = static_cast<TH1 *>(reader->Get("hXsection")),
	     eventhist = static_cast<TH1 *>(reader->Get("hNevents"));
	double weight = getweight(xsechist, eventhist);

	std::vector<TString> excludelist = {"hNevents", "hXsection", "hTrials"};
	for(auto obj : TRangeDynCast<TKey>(reader->GetListOfKeys())) {
		TString keyname = obj->GetName();
		TObject *object = obj->ReadObj();
		writer->cd();
		if(std::find(excludelist.begin(), excludelist.end(), obj->GetName()) == excludelist.end()) {
			std::cout << "Processing " << keyname << std::endl;
			auto col = dynamic_cast<TDirectory *>(object);
			if(col) {
				std::cout << "Recursive scaling for " << obj->GetName() << std::endl;
				reader->cd(keyname.Data());
				auto keys = gDirectory->GetListOfKeys();
				writer->mkdir(keyname.Data());
				writer->cd(keyname.Data());
				for(auto key : TRangeDynCast<TKey>(keys)) {
					auto obj1 = key->ReadObj();					
					auto hist = dynamic_cast<TH1 *>(obj1);
					if(hist) {
						hist->Scale(weight);
					} else {
						auto sparse = dynamic_cast<THnSparse *>(obj1);
						if(sparse){
							sparse->Scale(weight);
						}

					}
					obj1->Write();
				}
			} else {
				auto hist = dynamic_cast<TH1 *>(object);
				if(hist) {
					hist->Scale(weight);
				} else {
					auto sparse = dynamic_cast<THnSparse *>(object);
					if(sparse){
						sparse->Scale(weight);
					}
				}
				object->Write();
			}
		} else {
			std::cout << "Not scaling " << obj->GetName() << " because it is a scaling histogram" << std::endl;
			object->Write();
		}
	}
}