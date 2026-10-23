//Sample textures
	vec4 albedo_tex = texture2D(texture, texcoord);
	vec4 normal_tex = texture2D(normals, texcoord);
	vec4 specular_tex = texture2D(specular, texcoord);	
	
//Gamma correction - Optional if you're not doing gamma correct lighting	
	albedo_tex.xyz = pow(albedo_tex.xyz, vec3(2.2));
		
//Normals
	vec3 normal;
	normal.xy = normal_tex.xy * 2.0 - 1.0; //Bring to -1 - 1 range
	normal.z = sqrt(1.0-dot(normal.xy, normal.xy)); //Reconstruct Z
	normal = tbn_matrix * normal; //Rotate by TBN matrix
	normal = normal * 0.5 + 0.5; //0 - 1 range, buffers can't support negative values

//Ambient occlusion
	float ao = normal_tex.z;
	
//Heightmap
	float heightmap = normal_tex.w;
	
//Roughness - Converted from perceptural smoothness
	float roughness = pow(1.0 - specular_tex.x, 2.0);
	
//F0
	float F0 = specular_tex.y;
	
//Is our material metal? 
	bool is_metal = (specular_tex.y * 255.0) > 229.5;

//Subsurface and porosity
	float subsurface = 0.0;
	float porosity = 0.0;
	
//In case of future LabPBR versions, let's check for metals here
	if(!is_metal)
	{
		//Thickness
		subsurface = (specular_tex.z * 255.0) < 65.0 ? 0.0 : specular_tex.z;

		//Porosity
		porosity = (specular_tex.z * 255.0) > 64.0 ? 0.0 : specular_tex.z;
	}
    
//Emmision
	float emmision = (specular_tex.w * 255.0) < 254.5 ? specular_tex.w : 0.0;
	