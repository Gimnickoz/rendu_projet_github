create table combined_projet (
	from_stop INT,
	to_stop INT,
	dist_brut INT,
	duration_moy NUMERIC (10,6),
	n_vehicles INT,
	route_I INT,
	route_type INT,
	primary key (from_stop, to_stop, route_I,route_type)
);
