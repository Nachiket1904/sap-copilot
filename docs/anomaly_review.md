# Anomaly rule review (Week 3 Day 3)

Reviewed against `data/mock_sap/payments.csv` and `purchase_orders.csv`. Rules are in `src/data_layer/anomaly.py`.
Draft prepared by Nachiket's assistant from the data; the collaborator should confirm or overrule each point from SAP experience.

1. **Do the 6 flagged payments look unusual?** They are 26 to 35 days past due (PMT00028 35, PMT00151 33,
   PMT00102 32, PMT00093 30, PMT00103 26, PMT00112 26). Overall the mean payment is 10.8 days *early*, so these are
   far from normal. Two vendors appear more than once (Northgate Stationery twice) which makes them stronger
   candidates for follow-up than a one-off.
2. **Is 2σ the right threshold?** 2σ (24.6 days) gives 6 flags; 1.5σ gives 13, too many to review. A fixed rule
   "more than 30 days late" would flag only 3 and miss the 26-day payments that are still unusual against this data.
   Keep 2σ for now; revisit with more data.
3. **Missed cases:** payments that are only a little late but very large are not flagged, because the delay rule ignores
   amount. Also the 5 Scheduled payments have no payment date, so they cannot be checked until they are paid.
4. **False positives:** none obvious in the mock data. Real vendors with agreed long terms would be a risk in real data,
   since the rule uses one overall mean, not each vendor's own terms.
5. **Open for the collaborator:** does a 26-day delay count as "normal" for any vendor category in real SAP?
